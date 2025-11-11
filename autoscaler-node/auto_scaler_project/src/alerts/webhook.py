import requests
import datetime

def send_terminating_instances_webhook(instances, WEBHOOK_URL, reason, project):
    terminating = [i for i in instances if i.state == "Terminating" or i.state == "Terminated"]
    if not terminating:
        return  # no terminating instances

    for inst in terminating:
        payload = {
            "title": "🔴 OCI Instance Termination Detected",
            "project": project,
            "instance": inst.display_name,
            "region": inst.region.replace("_", "-"),
            "availability_domain": inst.availability_domain,
            "shape": inst.shape,
            "compartment": inst.compartment_id,
            "private_ip": "N/A",
            "started_at": datetime.datetime.now().strftime("%c"),
            "reason": reason,
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
 