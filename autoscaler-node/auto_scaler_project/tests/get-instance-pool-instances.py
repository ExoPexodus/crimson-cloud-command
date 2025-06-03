# This is an automatically generated code sample.
# To make this code sample work in your Oracle Cloud tenancy,
# please replace the values for any parameters whose current values do not fit
# your use case (such as resource IDs, strings containing ‘EXAMPLE’ or ‘unique_id’, and
# boolean, number, and enum parameters with values not fitting your use case).

import oci

# Create a default config using DEFAULT profile in default location
# Refer to
# https://docs.cloud.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm#SDK_and_CLI_Configuration_File
# for more info
config = oci.config.from_file()


# Initialize service client with default config file
core_client = oci.core.ComputeManagementClient(config)


# doc for more info
list_instance_pool_instances_response = core_client.list_instance_pool_instances(
    compartment_id="ocid1.compartment.oc1..aaaaaaaatey3m2mka7tfwmm2syaa4lquyeqdqem36qfxyfghxylquiq3qx5q",
    instance_pool_id="ocid1.instancepool.oc1.ap-mumbai-1.aaaaaaaa4xvc4uehki2wh2fqk7m47t7j6qy4f75swhzcli7ofszrxxswwaea",
    sort_order="ASC")

# Get the data from response
print(list_instance_pool_instances_response.data)