import logging
from oracle_sdk_wrapper.oci_scaling import scale_up, scale_down

def evaluate_metrics(collector, thresholds, scaling_limits, scheduler_active_callback):
    """
    Evaluate metrics and scale the instance pool as needed.

    Args:
        collector (MetricsCollector): Metrics collector object.
        thresholds (dict): Threshold values for CPU and RAM.
        scaling_limits (dict): Limits for scaling (min and max instance count).
        scheduler_active_callback (Callable): Function to check if the scheduler is active.

    Returns:
        dict: Scaling decision with scaling_event, scaling_reason, previous_instances, new_instances, and success
    """
    try:
        avg_cpu, avg_ram = collector.get_metrics()

        if avg_cpu < 0 or avg_ram < 0:
            logging.error(
                f"Invalid metrics received: CPU={avg_cpu}, RAM={avg_ram}. Skipping scaling."
            )
            return {
                'scaling_event': None,
                'scaling_reason': f'Invalid metrics: CPU={avg_cpu}, RAM={avg_ram}',
                'previous_instances': None,
                'new_instances': None,
                'success': False
            }

        if avg_cpu == 0 and avg_ram == 0:
            logging.warning(
                f"No valid metric data available for pool {collector.instance_pool_id}. Skipping scaling."
            )
            return {
                'scaling_event': None,
                'scaling_reason': 'No valid metric data available',
                'previous_instances': None,
                'new_instances': None,
                'success': False
            }

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
            result = scale_up(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["max"],
            )
            return {
                'scaling_event': result['action'] if result['action'] != 'NO_CHANGE' else None,
                'scaling_reason': f"Pool size ({current_size}) below minimum limit ({scaling_limits['min']})",
                'previous_instances': result.get('previous_size'),
                'new_instances': result.get('new_size'),
                'success': result['success']
            }

        if current_size > scaling_limits["max"]:
            logging.warning(
                f"Current size ({current_size}) exceeds the maximum limit ({scaling_limits['max']}). "
                "Prioritizing scaling down."
            )
            reason = f"Current pool size ({current_size}) exceeds the maximum limit ({scaling_limits['max']})."
            result = scale_down(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["min"],
                reason
            )
            return {
                'scaling_event': result['action'] if result['action'] != 'NO_CHANGE' else None,
                'scaling_reason': reason,
                'previous_instances': result.get('previous_size'),
                'new_instances': result.get('new_size'),
                'success': result['success']
            }

        # Check CPU and RAM thresholds only if instance count is within limits
        if avg_cpu > thresholds["cpu"]["max"] or avg_ram > thresholds["ram"]["max"]:
            logging.info("CPU or RAM exceeds thresholds, checking for scaling up...")
            reason = (
                f"CPU or RAM exceeded thresholds. "
                f"CPU {avg_cpu}% (max {thresholds['cpu']['max']}%), "
                f"RAM {avg_ram}% (max {thresholds['ram']['max']}%)"
            )
            result = scale_up(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["max"],
            )
            return {
                'scaling_event': result['action'] if result['action'] != 'NO_CHANGE' else None,
                'scaling_reason': reason,
                'previous_instances': result.get('previous_size'),
                'new_instances': result.get('new_size'),
                'success': result['success']
            }
            
        elif avg_cpu < thresholds["cpu"]["min"] or avg_ram < thresholds["ram"]["min"]:
            logging.info("CPU or RAM is below thresholds, checking for scaling down...")
            # Check if the scheduler is active before considering scaling down
            if scheduler_active_callback():
                logging.info("Scheduler is active. Temporarily preventing scaling down.")
                return {
                    'scaling_event': None,
                    'scaling_reason': 'Scaling down blocked by active scheduler',
                    'previous_instances': current_size,
                    'new_instances': current_size,
                    'success': True
                }
            reason = (
                f"CPU or RAM below thresholds. "
                f"CPU {avg_cpu}% (min {thresholds['cpu']['min']}%), "
                f"RAM {avg_ram}% (min {thresholds['ram']['min']}%)"
            )

            result = scale_down(
                collector.compute_management_client,
                collector.instance_pool_id,
                collector.compartment_id,
                scaling_limits["min"],
                reason
            )
            return {
                'scaling_event': result['action'] if result['action'] != 'NO_CHANGE' else None,
                'scaling_reason': reason,
                'previous_instances': result.get('previous_size'),
                'new_instances': result.get('new_size'),
                'success': result['success']
            }
        else:
            logging.info("No scaling required: Metrics are within thresholds.")
            return {
                'scaling_event': None,
                'scaling_reason': None,
                'previous_instances': current_size,
                'new_instances': current_size,
                'success': True
            }
            
    except Exception as e:
        logging.error(
            f"Error during metrics evaluation for pool {collector.instance_pool_id}: {e}"
        )
        return {
            'scaling_event': None,
            'scaling_reason': f'Error during evaluation: {str(e)}',
            'previous_instances': None,
            'new_instances': None,
            'success': False
        }
