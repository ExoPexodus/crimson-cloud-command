import os
import yaml
import logging

def load_yaml_config(file_path="config.yaml"):
    # Load the YAML file
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def get_region_from_pool(config, pool_index=0):
    """Fetch the region for the specified pool from the YAML config."""
    try:
        # Access the pools and get the region for the specified pool
        return config["pools"][pool_index]["region"]
    except KeyError:
        raise KeyError("Region not found for the specified pool.")
