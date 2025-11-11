import oci
import logging
import time
import sys
import os
from oci.core import ComputeManagementClient
from instance_manager.instance_pool import get_instance_pool_details, get_instances_from_instance_pool
from user_config.config_manager import build_oci_config  # Ensure to use this
from alerts.webhook import send_terminating_instances_webhook

def initialize_oci_client(config):
    return ComputeManagementClient(config)

def scale_up(compute_management_client, instance_pool_id, compartment_id, max_limit):
    try:
        # Fetch current instance pool details
        pool_details = get_instance_pool_details(compute_management_client,instance_pool_id)
        current_size = pool_details.size

        if current_size >= max_limit:
            logging.warning(
                f"Cannot scale up: Current size ({current_size}) has reached or exceeded the maximum limit ({max_limit})."
            )
            return

        # Update the instance pool size (scale up)
        new_size = current_size + 1
        logging.info(f"Scaling up instance pool {instance_pool_id} to {new_size}")
        compute_management_client.update_instance_pool(
            instance_pool_id=instance_pool_id,
            update_instance_pool_details=oci.core.models.UpdateInstancePoolDetails(size=new_size),
        )

        logging.info(f"Scaled up: Target instance count updated to {new_size}")
        logging.info("Waiting for 15 minutes after scaling up...")
        time.sleep(900)
    except Exception as e:
        logging.error(f"Failed to scale up: {str(e)}")
        sys.exit(1)

def scale_down(compute_management_client, instance_pool_id, compartment_id, min_limit, reason="scaling down"):
    try:
        # Fetch current instance pool details
        pool_details = get_instance_pool_details(compute_management_client, instance_pool_id=instance_pool_id)
        current_size = pool_details.size

        if current_size <= min_limit:
            logging.warning(
                f"Cannot scale down: Current size ({current_size}) has reached or is below the minimum limit ({min_limit})."
            )
            return

        # Update the instance pool size (scale down)
        new_size = current_size - 1
        logging.info(f"Scaling down instance pool {instance_pool_id} to {new_size}")
        compute_management_client.update_instance_pool(
            instance_pool_id=instance_pool_id,
            update_instance_pool_details=oci.core.models.UpdateInstancePoolDetails(size=new_size),
        )

        logging.info(f"Scaled down: Target instance count updated to {new_size}")
        logging.info("Waiting for 15 seconds before triggering the alert webhook...")
        time.sleep(15)
        
        instances = get_instances_from_instance_pool(compute_management_client, instance_pool_id, compartment_id)
        send_terminating_instances_webhook(instances, os.getenv("WEBHOOK_URL"), reason, os.getenv("PROJECT_NAME") )

        logging.info("Waiting for 15 minutes after scaling down...")
        time.sleep(880)

    except Exception as e:
        logging.error(f"Failed to scale down: {str(e)}")
        sys.exit(1)