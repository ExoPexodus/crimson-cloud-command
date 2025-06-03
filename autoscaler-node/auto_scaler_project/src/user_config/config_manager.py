import os
from .yaml_loader import load_yaml_config
import logging
import json
from dotenv import load_dotenv

def load_config(file_path="config.yaml"):
    return load_yaml_config(file_path)

def build_oci_config(selected_region):
    load_dotenv()

    region_map = json.loads(os.getenv("REGION_MAP"))
    actual_region = region_map.get(selected_region, None)

    logging.debug(f"Selected region: {selected_region}, Mapped region: {actual_region}")

    config = {
        "tenancy": os.getenv("TENANCY_OCID"),
        "user": os.getenv("USER_OCID"),
        "fingerprint": os.getenv("FINGERPRINT"),
        "key_file": os.getenv("PRIVATE_KEY_PATH"),
        "region": actual_region,
    }

    missing = [key for key, value in config.items() if value is None]
    if missing:
        logging.error(f"Missing required OCI config parameters: {', '.join(missing)}")
        raise ValueError(f"Missing required OCI config parameters: {', '.join(missing)}")

    logging.debug(f"Built OCI config: {config}")
    return config
