import json
import os
import logging
import datetime
from instance_manager.instance_pool import get_instances_from_instance_pool
from alerts.webhook import send_instance_alert

SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "instance_snapshots")


def _get_snapshot_path(pool_id):
    """Get the file path for a pool's snapshot file."""
    # Sanitize pool_id for use as filename (replace dots and colons)
    safe_id = pool_id.replace(".", "_").replace(":", "_")
    return os.path.join(SNAPSHOT_DIR, f"{safe_id}.json")


def load_snapshot(pool_id):
    """
    Load the previous instance snapshot from disk.
    
    Args:
        pool_id: The OCI instance pool ID
        
    Returns:
        dict: Mapping of instance_id -> instance_data, or empty dict on first run
    """
    path = _get_snapshot_path(pool_id)
    
    if not os.path.exists(path):
        logging.info(f"No previous snapshot found for pool {pool_id} (first run)")
        return {}
    
    try:
        with open(path, "r") as f:
            data = json.load(f)
        logging.debug(f"Loaded snapshot for pool {pool_id}: {len(data)} instances")
        return data
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Failed to load snapshot for pool {pool_id}: {e}")
        return {}


def save_snapshot(pool_id, instances):
    """
    Save the current instance list to a snapshot file on disk.
    
    Args:
        pool_id: The OCI instance pool ID
        instances: List of OCI instance objects from list_instance_pool_instances
    """
    # Ensure snapshot directory exists
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    
    snapshot = {}
    for inst in instances:
        # Only snapshot instances that are running/provisioning (alive)
        if inst.state in ("RUNNING", "Running", "Provisioning", "PROVISIONING"):
            region_formatted = inst.region.replace("_", "-") if inst.region and isinstance(inst.region, str) else inst.region or "unknown"
            snapshot[inst.id] = {
                "instance_id": inst.id,
                "display_name": inst.display_name or "unknown",
                "state": inst.state,
                "region": region_formatted,
                "availability_domain": inst.availability_domain or "unknown",
                "shape": inst.shape or "unknown",
                "compartment_id": inst.compartment_id or "unknown",
            }
    
    path = _get_snapshot_path(pool_id)
    try:
        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2)
        logging.debug(f"Saved snapshot for pool {pool_id}: {len(snapshot)} instances")
    except IOError as e:
        logging.error(f"Failed to save snapshot for pool {pool_id}: {e}")


def detect_changes(previous, current):
    """
    Compare two snapshots and detect which instances were terminated or created.
    
    Args:
        previous: dict of instance_id -> instance_data (from previous snapshot)
        current: dict of instance_id -> instance_data (from current OCI query)
        
    Returns:
        dict with keys:
            "terminated": list of instance_data dicts for instances that disappeared
            "created": list of instance_data dicts for instances that are new
    """
    prev_ids = set(previous.keys())
    curr_ids = set(current.keys())
    
    terminated_ids = prev_ids - curr_ids
    created_ids = curr_ids - prev_ids
    
    terminated = [previous[iid] for iid in terminated_ids]
    created = [current[iid] for iid in created_ids]
    
    return {
        "terminated": terminated,
        "created": created,
    }


def check_and_alert(pool_id, compute_management_client, compartment_id):
    """
    Main orchestrator: load previous snapshot, fetch current instances,
    diff them, fire webhooks as configured, save new snapshot.
    
    Args:
        pool_id: The OCI instance pool ID
        compute_management_client: OCI ComputeManagementClient instance
        compartment_id: The OCI compartment ID
    """
    webhook_url = os.getenv("WEBHOOK_URL")
    project_name = os.getenv("PROJECT_NAME", "unknown")
    alert_scale_down = os.getenv("WEBHOOK_ALERT_SCALE_DOWN", "true").lower() == "true"
    alert_scale_up = os.getenv("WEBHOOK_ALERT_SCALE_UP", "false").lower() == "true"
    
    # Load previous snapshot
    previous = load_snapshot(pool_id)
    
    # Fetch current instances from OCI
    try:
        instances = get_instances_from_instance_pool(
            compute_management_client, pool_id, compartment_id
        )
    except RuntimeError as e:
        logging.error(f"Failed to fetch instances for state tracking: {e}")
        return
    
    # Build current snapshot dict (only alive instances)
    current = {}
    for inst in instances:
        if inst.state in ("RUNNING", "Running", "Provisioning", "PROVISIONING"):
            region_formatted = inst.region.replace("_", "-") if inst.region and isinstance(inst.region, str) else inst.region or "unknown"
            current[inst.id] = {
                "instance_id": inst.id,
                "display_name": inst.display_name or "unknown",
                "state": inst.state,
                "region": region_formatted,
                "availability_domain": inst.availability_domain or "unknown",
                "shape": inst.shape or "unknown",
                "compartment_id": inst.compartment_id or "unknown",
            }
    
    # If no previous snapshot exists (first run), just save and return
    if not previous:
        logging.info(f"First snapshot for pool {pool_id}: {len(current)} running instances recorded")
        save_snapshot(pool_id, instances)
        return
    
    # Detect changes
    changes = detect_changes(previous, current)
    
    terminated = changes["terminated"]
    created = changes["created"]
    
    if terminated:
        logging.info(f"Detected {len(terminated)} terminated instance(s) in pool {pool_id}: "
                     f"{[i['display_name'] for i in terminated]}")
    if created:
        logging.info(f"Detected {len(created)} new instance(s) in pool {pool_id}: "
                     f"{[i['display_name'] for i in created]}")
    
    if not terminated and not created:
        logging.debug(f"No instance changes detected for pool {pool_id}")
    
    # Fire webhooks if configured
    if webhook_url:
        if alert_scale_down and terminated:
            for inst_data in terminated:
                logging.info(f"🔴 Sending termination alert for {inst_data['display_name']}")
                send_instance_alert(inst_data, webhook_url, project_name, "scale_down")
        
        if alert_scale_up and created:
            for inst_data in created:
                logging.info(f"🟢 Sending creation alert for {inst_data['display_name']}")
                send_instance_alert(inst_data, webhook_url, project_name, "scale_up")
    elif terminated or created:
        logging.warning("WEBHOOK_URL not configured, skipping instance change alerts")
    
    # Save current snapshot (always, regardless of webhook config)
    save_snapshot(pool_id, instances)
