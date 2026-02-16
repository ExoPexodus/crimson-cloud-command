import requests
import datetime
import logging
import json

def send_terminating_instances_webhook(instances, WEBHOOK_URL, reason, project):
    terminating = [i for i in instances if i.state == "Terminating" or i.state == "Terminated"]
    if not terminating:
        return  # no terminating instances

    for inst in terminating:
        # Safe region string manipulation
        region_formatted = inst.region.replace("_", "-") if inst.region and isinstance(inst.region, str) else inst.region or "unknown"
        
        payload = {
            "title": "🔴 OCI Instance Termination Detected",
            "project": project or "unknown",
            "instance": inst.display_name or "unknown",
            "region": region_formatted,
            "availability_domain": inst.availability_domain or "unknown",
            "shape": inst.shape or "unknown",
            "compartment": inst.compartment_id or "unknown",
            "private_ip": "N/A",
            "started_at": datetime.datetime.now().strftime("%c"),
            "reason": reason or "No reason provided",
        }

        # Log the payload being sent
        logging.info(f"📤 Preparing webhook for instance: {inst.display_name}")
        logging.debug(f"📋 Webhook payload: {json.dumps(payload, indent=2)}")
        
        try:
            logging.info(f"🔗 Sending webhook to: {WEBHOOK_URL}")
            r = requests.post(
                WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # Log response details
            logging.info(f"📨 Webhook response status: {r.status_code}")
            logging.debug(f"📨 Response headers: {dict(r.headers)}")
            
            try:
                response_body = r.text
                logging.debug(f"📨 Response body: {response_body[:500]}")  # First 500 chars
            except:
                logging.debug("📨 Response body could not be read")
            
            r.raise_for_status()
            logging.info(f"✅ Successfully sent webhook alert for {inst.display_name}")
            
        except requests.exceptions.Timeout as e:
            logging.error(f"❌ Webhook timeout after 10s for {inst.display_name}: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"❌ Webhook connection error for {inst.display_name}: {str(e)}")
        except requests.exceptions.HTTPError as e:
            logging.error(f"❌ Webhook HTTP error {r.status_code} for {inst.display_name}: {str(e)}")
            logging.error(f"❌ Response body: {r.text[:500]}")
        except Exception as e:
            logging.error(f"❌ Webhook unexpected error for {inst.display_name}: {type(e).__name__} - {str(e)}")


def send_instance_alert(instance_data, webhook_url, project, event_type):
    """
    Send a webhook alert for an instance state change.
    Accepts a plain dict (from the state tracker snapshot diff) instead of OCI SDK objects.
    
    Args:
        instance_data: dict with keys: display_name, region, availability_domain, shape, compartment_id
        webhook_url: The webhook URL to POST to
        project: Project name string
        event_type: "scale_down" or "scale_up"
    """
    if event_type == "scale_down":
        title = "🔴 OCI Instance Termination Detected"
        reason = "Instance no longer present in pool (scale-down)"
    elif event_type == "scale_up":
        title = "🟢 OCI Instance Creation Detected"
        reason = "New instance detected in pool (scale-up)"
    else:
        title = "⚠️ OCI Instance State Change Detected"
        reason = f"Instance state change: {event_type}"

    payload = {
        "title": title,
        "project": project or "unknown",
        "instance": instance_data.get("display_name", "unknown"),
        "region": instance_data.get("region", "unknown"),
        "availability_domain": instance_data.get("availability_domain", "unknown"),
        "shape": instance_data.get("shape", "unknown"),
        "compartment": instance_data.get("compartment_id", "unknown"),
        "private_ip": "N/A",
        "started_at": datetime.datetime.now().strftime("%c"),
        "reason": reason,
    }

    instance_name = instance_data.get("display_name", "unknown")
    logging.info(f"📤 Preparing {event_type} alert for instance: {instance_name}")
    logging.debug(f"📋 Alert payload: {json.dumps(payload, indent=2)}")

    try:
        logging.info(f"🔗 Sending alert to: {webhook_url}")
        r = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        logging.info(f"📨 Alert response status: {r.status_code}")
        logging.debug(f"📨 Response headers: {dict(r.headers)}")

        try:
            response_body = r.text
            logging.debug(f"📨 Response body: {response_body[:500]}")
        except:
            logging.debug("📨 Response body could not be read")

        r.raise_for_status()
        logging.info(f"✅ Successfully sent {event_type} alert for {instance_name}")

    except requests.exceptions.Timeout as e:
        logging.error(f"❌ Alert timeout after 10s for {instance_name}: {str(e)}")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"❌ Alert connection error for {instance_name}: {str(e)}")
    except requests.exceptions.HTTPError as e:
        logging.error(f"❌ Alert HTTP error {r.status_code} for {instance_name}: {str(e)}")
        logging.error(f"❌ Response body: {r.text[:500]}")
    except Exception as e:
        logging.error(f"❌ Alert unexpected error for {instance_name}: {type(e).__name__} - {str(e)}")