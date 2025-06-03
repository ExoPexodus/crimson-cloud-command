import logging
import time
import os
from collectors.prometheus_collector import PrometheusMetricsCollector
from collectors.oci_collector import OCIMetricsCollector
from user_config.config_manager import build_oci_config, load_yaml_config
from scaling_logic.auto_scaler import evaluate_metrics
from oracle_sdk_wrapper.oci_scaling import initialize_oci_client
from instance_manager.instance_pool import get_instances_from_instance_pool
from oci.monitoring import MonitoringClient
from oci.core import ComputeManagementClient
from scheduler.scheduler import Scheduler  # Importing Scheduler
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("autoscaling.log"),
        logging.StreamHandler()  # Output logs to the console
    ],
)


def get_collector(pool, compute_management_client, monitoring_client):
    """
    Factory function to get the correct MetricsCollector based on the monitoring method.

    Args:
        pool (dict): Pool configuration details from the YAML file.
        compute_management_client: OCI ComputeManagementClient instance.
        monitoring_client: OCI MonitoringClient instance.

    Returns:
        MetricsCollector instance.
    """
    logging.debug(
        f"Creating collector for pool={pool['instance_pool_id']} "
        f"using compute_management_client={type(compute_management_client)} and monitoring_client={type(monitoring_client)}"
    )
    monitoring_method = pool.get("monitoring_method")
    if monitoring_method == "prometheus":
        return PrometheusMetricsCollector(
            prometheus_url=pool["prometheus_url"],
            compute_management_client=compute_management_client,
            instance_pool_id=pool["instance_pool_id"],
            compartment_id=pool["compartment_id"],
        )
    elif monitoring_method == "oci":
        # Use ComputeManagementClient to fetch instance data
        return OCIMetricsCollector(
            monitoring_client=monitoring_client,
            compute_management_client=compute_management_client,  # Pass both clients
            instance_manager=get_instances_from_instance_pool,
            instance_pool_id=pool["instance_pool_id"],
            compartment_id=pool["compartment_id"],
        )
    else:
        raise ValueError(f"Unknown monitoring method: {monitoring_method}")


def process_pool(pool):
    """
    Process a single pool for monitoring and scaling.

    Args:
        pool (dict): Pool configuration details from the YAML file.
    """
    region = pool.get("region")
    if not region:
        logging.error(
            f"Region not specified for pool {pool['instance_pool_id']}. Skipping."
        )
        return

    # Build OCI clients for the pool
    try:
        oci_config = build_oci_config(region)
        compute_management_client = ComputeManagementClient(
            oci_config
        )
        monitoring_client = MonitoringClient(
            oci_config
        )
    except Exception as e:
        logging.error(f"Failed to initialize OCI clients for region {region}: {e}")
        raise RuntimeError(f"OCI client initialization failed for region {region}: {e}")

    # Create the appropriate collector
    try:
        collector = get_collector(pool, compute_management_client, monitoring_client)
    except ValueError as ve:
        logging.error(ve)
        raise RuntimeError(
            f"Collector creation failed for pool {pool['instance_pool_id']}: {ve}"
        )

    # Define thresholds
    thresholds = {
        "cpu": pool["cpu_threshold"],
        "ram": pool["ram_threshold"],
    }

    # Define scaling limits
    scaling_limits = pool["scaling_limits"]

    # Initialize and start the Scheduler
    max_instances = scaling_limits["max"]
    schedules = pool["schedules"]  # List of schedule dictionaries
    scheduler_instances = pool["scheduler_max_instances"]

    scheduler = Scheduler(
        compute_management_client=compute_management_client,
        instance_pool_id=pool["instance_pool_id"],
        max_instances=max_instances,
        schedules=schedules,
        scheduler_instances=scheduler_instances
    )
    scheduler.start()


    # function to determine whether the scheduler is active or not
    def scheduler_active_callback():
        return scheduler.is_active()

    # Monitor and scale
    try:
        logging.info(f"Starting monitoring loop for pool: {pool['instance_pool_id']}")
        while True:
            try:
                # Pass scaling_limits to evaluate_metrics
                evaluate_metrics(collector, thresholds, scaling_limits, scheduler_active_callback)
            except RuntimeError as e:
                logging.error(f"Runtime error in evaluate_metrics: {e}")
                raise  # Re-raise to stop further execution
            time.sleep(300)  # Sleep for 5 minutes between checks
    except KeyboardInterrupt:
        logging.info(f"Terminating monitoring for pool: {pool['instance_pool_id']}")
    except Exception as e:
        logging.error(
            f"Error in autoscaling loop for pool {pool['instance_pool_id']}: {e}"
        )
        raise RuntimeError(
            f"Critical failure in autoscaling for pool {pool['instance_pool_id']}: {e}"
        )
    
    finally:
        scheduler.stop()  # Ensure the scheduler stops gracefully when monitoring ends


def main():
    logging.info("Starting autoscaling process...")

    # Load configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.yaml"
    )
    logging.debug(f"Loading configuration from: {config_path}")
    try:
        config = load_yaml_config(config_path)
    except Exception as e:
        logging.error(f"Failed to load configuration file: {e}")
        raise RuntimeError(f"Configuration file load failed: {e}")

    # Process each pool from the configuration
    for pool in config["pools"]:
        logging.debug(f"Starting processing for pool: {pool}")
        try:
            process_pool(pool)
        except RuntimeError as re:
            logging.error(f"Error processing pool {pool['instance_pool_id']}: {re}")
            continue  # Skip to the next pool
        logging.debug(f"Loaded pools from config: {config.get('pools')}")
        


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        logging.error(f"Runtime error during execution: {e}")
