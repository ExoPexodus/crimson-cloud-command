from prometheus_metrics.prometheus_client import get_cpu_ram_metrics
from collectors.base_collector import MetricsCollector
from instance_manager.instance_pool import get_instances_from_instance_pool
import logging


class PrometheusMetricsCollector(MetricsCollector):
    def __init__(self, prometheus_url, compute_management_client, instance_pool_id, compartment_id):
        """
        Initialize the Prometheus Metrics Collector.

        Args:
            prometheus_url (str): URL of the Prometheus server.
            compute_management_client: OCI ComputeManagementClient instance.
            instance_pool_id (str): OCID of the instance pool.
            compartment_id (str): OCID of the compartment.
        """
        self.prometheus_url = prometheus_url
        self.compute_management_client = compute_management_client
        self.instance_pool_id = instance_pool_id
        self.compartment_id = compartment_id

        logging.debug(f"Initialized PrometheusMetricsCollector with URL: {self.prometheus_url}, "
                      f"instance_pool_id: {self.instance_pool_id}, compartment_id: {self.compartment_id}")

    def get_metrics(self):
        """
        Fetch average CPU and RAM utilization across all instances in the pool.

        Returns:
            Tuple (avg_cpu_utilization, avg_memory_utilization).
        Raises:
            RuntimeError: If metrics cannot be fetched for any critical reason.
        """
        try:
            # Fetch the instances in the pool
            instances = get_instances_from_instance_pool(
                self.compute_management_client, self.instance_pool_id, self.compartment_id
            )

            if not instances:
                raise RuntimeError(f"No instances found in pool {self.instance_pool_id}. Terminating execution.")

            logging.debug(f"Fetched instances: {[instance.display_name for instance in instances]}")

            total_cpu = 0
            total_ram = 0
            instance_count = len(instances)

            # Fetch metrics for each instance using its hostname
            for instance in instances:
                instance_hostname = instance.display_name  # Using display_name as the hostname
                logging.debug(f"Fetching Prometheus metrics for instance hostname: {instance_hostname}")

                try:
                    cpu_data, ram_data = get_cpu_ram_metrics(instance_hostname, self.prometheus_url)

                    if not cpu_data or not ram_data:
                        raise RuntimeError(f"Metrics not found for instance {instance_hostname}.")
                    
                    total_cpu += float(cpu_data[0]['value'][1])
                    total_ram += float(ram_data[0]['value'][1])
                except Exception as metric_error:
                    raise RuntimeError(
                        f"Failed to fetch metrics for instance {instance_hostname}: {metric_error}"
                    )

            avg_cpu = total_cpu / instance_count if instance_count > 0 else 0
            avg_ram = total_ram / instance_count if instance_count > 0 else 0

            logging.info(f"Average CPU: {avg_cpu}%, Average RAM: {avg_ram}%")
            return avg_cpu, avg_ram

        except RuntimeError as re:
            logging.error(f"RuntimeError while fetching Prometheus metrics: {re}")
            raise  # Re-raise the RuntimeError to halt execution
        except Exception as e:
            logging.error(f"Unexpected error while fetching Prometheus metrics for pool {self.instance_pool_id}: {e}")
            raise RuntimeError(f"Critical failure in metrics collection: {e}")
