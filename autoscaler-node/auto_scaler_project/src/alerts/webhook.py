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
 