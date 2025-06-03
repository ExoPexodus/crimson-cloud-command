
import logging
import time
from user_config.config_manager import build_oci_config
from scaling_logic.auto_scaler import evaluate_metrics
from oci.monitoring import MonitoringClient
from oci.core import ComputeManagementClient
from scheduler.scheduler import Scheduler
from collector_factory import get_collector


def process_pool(pool, autoscaler_node):
    """
    Process a single pool for monitoring and scaling.

    Args:
        pool (dict): Pool configuration details from the YAML file.
        autoscaler_node (AutoscalerNode): The autoscaler node instance.
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
    schedules = pool.get("schedules", [])  # List of schedule dictionaries
    scheduler_instances = pool.get("scheduler_max_instances", max_instances)

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
                # Get metrics before scaling evaluation
                avg_cpu, avg_ram = collector.get_metrics()
                
                # Collect analytics data
                pool_details = collector.compute_management_client.get_instance_pool(
                    instance_pool_id=pool['instance_pool_id']
                ).data
                
                analytics_data = {
                    'current_instances': pool_details.size,
                    'active_instances': pool_details.size,  # Simplified for now
                    'avg_cpu_utilization': avg_cpu,
                    'avg_memory_utilization': avg_ram,
                    'max_cpu_utilization': avg_cpu,  # Simplified
                    'max_memory_utilization': avg_ram,  # Simplified
                    'pool_status': 'healthy',
                    'is_active': True,
                    'scaling_event': None,
                    'scaling_reason': None
                }
                
                # Add analytics to node for heartbeat
                autoscaler_node.add_pool_analytics(pool['instance_pool_id'], analytics_data)
                
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
