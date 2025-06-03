
import logging
import os
import hashlib
from user_config.config_manager import load_yaml_config
from autoscaler_node import AutoscalerNode
from pool_processor import process_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("autoscaling.log"),
        logging.StreamHandler()  # Output logs to the console
    ],
)


def main():
    logging.info("Starting autoscaling process...")

    # Load configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.yaml"
    )
    logging.debug(f"Loading configuration from: {config_path}")
    
    try:
        config = load_yaml_config(config_path)
        
        # Calculate config hash
        with open(config_path, 'r') as f:
            config_content = f.read()
        config_hash = hashlib.sha256(config_content.encode()).hexdigest()
        
    except Exception as e:
        logging.error(f"Failed to load configuration file: {e}")
        raise RuntimeError(f"Configuration file load failed: {e}")

    # Initialize autoscaler node with config
    autoscaler_node = AutoscalerNode(config)
    autoscaler_node.config_hash = config_hash

    # Start heartbeat service
    autoscaler_node.start_heartbeat()

    try:
        # Process each pool from the configuration
        for pool in config["pools"]:
            logging.debug(f"Starting processing for pool: {pool}")
            try:
                process_pool(pool, autoscaler_node)
            except RuntimeError as re:
                logging.error(f"Error processing pool {pool['instance_pool_id']}: {re}")
                continue  # Skip to the next pool
            logging.debug(f"Loaded pools from config: {config.get('pools')}")
    finally:
        # Stop heartbeat service on exit
        autoscaler_node.stop_heartbeat_service()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        logging.error(f"Runtime error during execution: {e}")
