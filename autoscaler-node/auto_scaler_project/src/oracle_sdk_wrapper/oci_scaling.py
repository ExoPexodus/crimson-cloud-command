import oci
import logging
from oci.core import ComputeManagementClient
from instance_manager.instance_pool import get_instance_pool_details, get_instances_from_instance_pool
from user_config.config_manager import build_oci_config  # Ensure to use this

def initialize_oci_client(config):
    return ComputeManagementClient(config)

def scale_up(compute_management_client, instance_pool_id, compartment_id, max_limit):
    """
    Scale up the instance pool by one instance.
    
    Returns:
        dict: Scaling result with action, previous_size, new_size, success, and reason
    """
    try:
        # Fetch current instance pool details
        pool_details = get_instance_pool_details(compute_management_client, instance_pool_id)
        current_size = pool_details.size

        if current_size >= max_limit:
            logging.warning(
                f"Cannot scale up: Current size ({current_size}) has reached or exceeded the maximum limit ({max_limit})."
            )
            return {
                'action': 'NO_CHANGE',
                'previous_size': current_size,
                'new_size': current_size,
                'success': False,
                'reason': f'At max limit ({max_limit})'
            }

        # Update the instance pool size (scale up)
        new_size = current_size + 1
        logging.info(f"Scaling up instance pool {instance_pool_id} to {new_size}")
        compute_management_client.update_instance_pool(
            instance_pool_id=instance_pool_id,
            update_instance_pool_details=oci.core.models.UpdateInstancePoolDetails(size=new_size),
        )

        logging.info(f"Scaled up: Target instance count updated to {new_size}")
        
        return {
            'action': 'SCALE_UP',
            'previous_size': current_size,
            'new_size': new_size,
            'success': True,
            'reason': 'Scaled up successfully'
        }
        
    except Exception as e:
        logging.error(f"Failed to scale up: {str(e)}")
        return {
            'action': 'SCALE_UP',
            'previous_size': None,
            'new_size': None,
            'success': False,
            'reason': f'Error: {str(e)}'
        }

def scale_down(compute_management_client, instance_pool_id, compartment_id, min_limit, reason="scaling down"):
    """
    Scale down the instance pool by one instance.
    
    Returns:
        dict: Scaling result with action, previous_size, new_size, success, and reason
    """
    try:
        # Fetch current instance pool details
        pool_details = get_instance_pool_details(compute_management_client, instance_pool_id=instance_pool_id)
        current_size = pool_details.size

        if current_size <= min_limit:
            logging.warning(
                f"Cannot scale down: Current size ({current_size}) has reached or is below the minimum limit ({min_limit})."
            )
            return {
                'action': 'NO_CHANGE',
                'previous_size': current_size,
                'new_size': current_size,
                'success': False,
                'reason': f'At min limit ({min_limit})'
            }

        # Update the instance pool size (scale down)
        new_size = current_size - 1
        logging.info(f"Scaling down instance pool {instance_pool_id} to {new_size}")
        compute_management_client.update_instance_pool(
            instance_pool_id=instance_pool_id,
            update_instance_pool_details=oci.core.models.UpdateInstancePoolDetails(size=new_size),
        )

        logging.info(f"Scaled down: Target instance count updated to {new_size}")

        return {
            'action': 'SCALE_DOWN',
            'previous_size': current_size,
            'new_size': new_size,
            'success': True,
            'reason': reason
        }

    except Exception as e:
        logging.error(f"Failed to scale down: {str(e)}")
        return {
            'action': 'SCALE_DOWN',
            'previous_size': None,
            'new_size': None,
            'success': False,
            'reason': f'Error: {str(e)}'
        }
