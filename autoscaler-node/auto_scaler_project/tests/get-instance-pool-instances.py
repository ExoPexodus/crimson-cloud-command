# This is an automatically generated code sample.
# To make this code sample work in your Oracle Cloud tenancy,
# please replace the values for any parameters whose current values do not fit
# your use case (such as resource IDs, strings containing ‘EXAMPLE’ or ‘unique_id’, and
# boolean, number, and enum parameters with values not fitting your use case).

import oci
import requests
import datetime
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


def send_terminating_instances_webhook(instances,WEBHOOK_URL):
    # Filter only the instances in "Terminating" state
    terminating = [i for i in instances if i.get("state") == "Terminating"]

    if not terminating:
        # Nothing is terminating, nothing to scream about
        return

    # Build payload for all terminating instances
    # You can change structure here if you want it fancier
    payload = {
        "title": "🟢 OCI Instance Termination Detected",
        "project": "oci-newkm",
        "started_at": datetime.datetime.now().strftime("%c"),
        "instances": []
    }

    for inst in terminating:
        payload["instances"].append({
            "display_name": inst.get("display_name"),
            "id": inst.get("id"),
            "availability_domain": inst.get("availability_domain"),
            "compartment_id": inst.get("compartment_id"),
            "region": inst.get("region"),
            "shape": inst.get("shape"),
            "fault_domain": inst.get("fault_domain"),
            "time_created": inst.get("time_created"),
            "instance_configuration_id": inst.get("instance_configuration_id")
        })

    try:
        r = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        r.raise_for_status()
    except Exception as e:
        print("Webhook failed:", e)



instances=list_instance_pool_instances_response
WEBHOOK_URL="https://defaultb20dfff0a92440e490b2b2045d9103.28.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/2b4fd24ea1b04297ab7a3d4bf8efda9d/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=zGwXahDL8cyASC3COBLObAXxNZ911u42OhSm1BqfXt8"
# Fire the webhook
send_terminating_instances_webhook(instances,WEBHOOK_URL)