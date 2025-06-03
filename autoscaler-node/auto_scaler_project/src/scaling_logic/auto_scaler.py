import logging
from oracle_sdk_wrapper.oci_scaling import scale_up, scale_down
import sys

def evaluate_metrics(collector, thresholds, scaling_limits, scheduler_active_callback):
    """
    Evaluate metrics and scale the instance pool as needed.

    Args:
        collector (MetricsCollector): Metrics collector object.
        thresholds (dict): Threshold values for CPU and RAM.
        scaling_limits (dict): Limits for scaling (min and max instance count).
        scheduler_active_callback (Callable): Function to check if the scheduler is active.
    """
    try:
        avg_cpu, avg_ram = collector.get_metrics()

        if avg_cpu < 0 or avg_ram < 0:
            logging.error(
                f"Invalid metrics received: CPU={avg_cpu}, RAM={avg_ram}. Skipping scaling."
            )
            return

        if avg_cpu == 0 and avg_ram == 0:
            logging.warning(
                f"No valid metric data available for pool {collector.instance_pool_id}. Skipping scaling."
            )
            return

        # Log metrics
        logging.info(f"Pool ID: {collector.instance_pool_id}")
        logging.info(f"Average CPU: {avg_cpu}%, Average RAM: {avg_ram}%")
        logging.info(f"Thresholds - CPU: {thresholds['cpu']}, RAM: {thresholds['ram']}")
        logging.info(
            f"Scaling Limits - Min: {scaling_limits['min']}, Max: {scaling_limits['max']}"
        )

        # Fetch current instance pool size
        current_size = collector.compute_management_client.get_instance_pool(
            instance_pool_id=collector.instance_pool_id
        ).data.size

        # Ensure instance count is within bounds
        if current_size < scaling_limits["min"]:
            logging.warning(
                f"Current size ({current_size}) is below the minimum limit ({scaling_limits['min']}). "
                "Prioritizing scaling up."
            )
            scale_up(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["max"],
            )
            return

        if current_size > scaling_limits["max"]:
            logging.warning(
                f"Current size ({current_size}) exceeds the maximum limit ({scaling_limits['max']}). "
                "Prioritizing scaling down."
            )
            scale_down(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["min"],
            )
            return

        # Check CPU and RAM thresholds only if instance count is within limits
        if avg_cpu > thresholds["cpu"]["max"] or avg_ram > thresholds["ram"]["max"]:
            logging.info("CPU or RAM exceeds thresholds, checking for scaling up...")
            scale_up(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["max"],
            )
        elif avg_cpu < thresholds["cpu"]["min"] or avg_ram < thresholds["ram"]["min"]:
            logging.info("CPU or RAM is below thresholds, checking for scaling down...")
            # Check if the scheduler is active before considering scaling down
            if scheduler_active_callback():
                logging.info("Scheduler is active. Temporarily preventing scaling down.")
                return
            scale_down(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["min"],
            )
        else:
            logging.info("No scaling required: Metrics are within thresholds.")
    except Exception as e:
        logging.error(
            f"Error during metrics evaluation for pool {collector.instance_pool_id}: {e}"
        )
        sys.exit(1)
