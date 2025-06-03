import oci
from datetime import datetime, timedelta

# Replace these with your values
compartment_id = "ocid1.compartment.oc1..aaaaaaaatey3m2mka7tfwmm2syaa4lquyeqdqem36qfxyfghxylquiq3qx5q"
instance_id = "ocid1.instance.oc1.ap-mumbai-1.anrg6ljrxwxldzacmrrkpvlaeosvi7gznvtt47qbsvkolgo4i3zfasm7ckzq"
namespace = "oci_computeagent"
instance_pool_id = "ocid1.instancepool.oc1.ap-mumbai-1.aaaaaaaa4xvc4uehki2wh2fqk7m47t7j6qy4f75swhzcli7ofszrxxswwaea"

# Initialize MonitoringClient
config = oci.config.from_file()  # Default config file ~/.oci/config
monitoring_client = oci.monitoring.MonitoringClient(config)
oci.config.DEFAULT_LOG_LEVEL = 'DEBUG'

# Set Time Range
end_time = datetime.utcnow()
start_time = end_time - timedelta(minutes=5)

# Define the query string with the correct format
query = f"CpuUtilization[5m]{{resourceId = \"{instance_id}\"}}.max()"
# Define the query string with the correct format
query = f"MemoryUtilization[5m]{{resourceId = \"{instance_id}\"}}.max()"

# Query for metrics using SummarizeMetricsDataDetails
try:
    response = monitoring_client.summarize_metrics_data(
        compartment_id=compartment_id,
        summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(
            namespace=namespace,
            query=query,  # Use query parameter
            start_time=start_time,
            end_time=end_time,
            resolution="5m"  # 1 minute resolution
        )
    )

    # Check if the response contains data and print
    if response.data:
        print("Metrics Data:")
        print(response.data)
    else:
        print("No data returned for the given query.")

except oci.exceptions.ServiceError as e:
    print("Service Error:", e)
