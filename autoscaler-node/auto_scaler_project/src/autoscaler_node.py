
import logging
import threading
import os
import hashlib
from services.heartbeat_service import HeartbeatService


class AutoscalerNode:
    def __init__(self, config):
        """Initialize the autoscaler node with backend integration."""
        # Get backend configuration from config file
        backend_config = config.get("backend", {})
        self.backend_url = backend_config.get("url", os.getenv("BACKEND_URL", "http://localhost:8000"))
        self.node_id = backend_config.get("node_id", 1)
        self.api_key = backend_config.get("api_key", os.getenv("API_KEY", ""))
        
        if not self.api_key:
            logging.warning("No API_KEY provided. Heartbeat service will be disabled.")
            self.heartbeat_service = None
        else:
            self.heartbeat_service = HeartbeatService(self.backend_url, self.node_id, self.api_key)
        
        self.heartbeat_thread = None
        self.stop_heartbeat = threading.Event()
        self.pool_analytics = []
        self.config_hash = None

    def start_heartbeat(self):
        """Start the heartbeat service in a separate thread."""
        if not self.heartbeat_service:
            return
            
        def heartbeat_loop():
            while not self.stop_heartbeat.is_set():
                try:
                    response = self.heartbeat_service.send_heartbeat(
                        status="active",
                        pool_analytics=self.pool_analytics,
                        config_hash=self.config_hash
                    )
                    
                    # Check if configuration update is needed
                    if response.get('config_update_needed'):
                        logging.info("Configuration update detected")
                        new_config = response.get('new_config')
                        if new_config:
                            self.update_configuration(new_config)
                    
                    # Clear pool analytics after sending
                    self.pool_analytics = []
                    
                except Exception as e:
                    logging.error(f"Heartbeat error: {e}")
                
                # Wait 60 seconds before next heartbeat
                self.stop_heartbeat.wait(60)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        logging.info("Heartbeat service started")

    def stop_heartbeat_service(self):
        """Stop the heartbeat service."""
        if self.heartbeat_thread:
            self.stop_heartbeat.set()
            self.heartbeat_thread.join()
            logging.info("Heartbeat service stopped")

    def update_configuration(self, yaml_config: str):
        """Update configuration and restart services if needed."""
        try:
            # Save new configuration
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config.yaml"
            )
            with open(config_path, 'w') as f:
                f.write(yaml_config)
            
            # Update config hash
            self.config_hash = hashlib.sha256(yaml_config.encode()).hexdigest()
            logging.info("Configuration updated successfully")
            
        except Exception as e:
            logging.error(f"Failed to update configuration: {e}")

    def add_pool_analytics(self, pool_id: str, analytics_data: dict):
        """Add pool analytics data to be sent with next heartbeat."""
        self.pool_analytics.append({
            'oracle_pool_id': pool_id,
            'pool_id': 1,  # This would need to be mapped from config
            **analytics_data
        })
