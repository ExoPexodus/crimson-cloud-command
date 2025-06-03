import oci
import logging

def get_instance_pool_details(compute_management_client, instance_pool_id):
    try:
        logging.info(f"Fetching details of {instance_pool_id}")
        response = compute_management_client.get_instance_pool(
            instance_pool_id=instance_pool_id
        ).data

        if response:
            return response
        else:
            logging.warning("Instance pool not found.")
            return []
    except Exception as e:
        logging.error(f"Failed to get instance pool details: {str(e)}")
        return [] 
def get_instances_from_instance_pool(compute_management_client, instance_pool_id, compartment_id):
    logging.debug(f"Fetching instances with compute_management_client={type(compute_management_client)}, "
                  f"instance_pool_id={instance_pool_id}, compartment_id={compartment_id}")
    try:
        response = compute_management_client.list_instance_pool_instances(
            compartment_id=compartment_id,
            instance_pool_id=instance_pool_id,
            sort_order="ASC"
        ).data

        if not response:
            raise RuntimeError(f"No instances found in pool {instance_pool_id}. Terminating execution.")

        logging.debug(f"Instances fetched successfully: {[instance.id for instance in response]}")
        return response
    except Exception as e:
        raise RuntimeError(f"Failed to fetch instance pool details: {e}")