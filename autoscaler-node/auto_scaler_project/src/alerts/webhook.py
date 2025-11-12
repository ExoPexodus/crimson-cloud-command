import requests
import datetime

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

        try:
            r = requests.post(
                WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            r.raise_for_status()
            print(f"✅ Sent Teams alert for {inst.display_name}")
        except Exception as e:  
            print("❌ Webhook failed:", e)
 