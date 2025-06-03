
import logging
from collectors.prometheus_collector import PrometheusMetricsCollector
from collectors.oci_collector import OCIMetricsCollector
from instance_manager.instance_pool import get_instances_from_instance_pool


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
