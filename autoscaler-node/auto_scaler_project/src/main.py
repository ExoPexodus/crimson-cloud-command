
import logging
import time
import os
import threading
import signal
import sys
from collectors.prometheus_collector import PrometheusMetricsCollector
from collectors.oci_collector import OCIMetricsCollector
from user_config.config_manager import build_oci_config, load_config, get_backend_config
from scaling_logic.auto_scaler import evaluate_metrics
from oracle_sdk_wrapper.oci_scaling import initialize_oci_client
from instance_manager.instance_pool import get_instances_from_instance_pool
from oci.monitoring import MonitoringClient
from oci.core import ComputeManagementClient
from scheduler.scheduler import Scheduler
from services.heartbeat_service import HeartbeatService
import hashlib
import socket

# Configure logging level from environment variable
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

logging.basicConfig(
    level=log_level_mapping.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("autoscaling.log"),
        logging.StreamHandler()  # Output logs to the console
    ],
)

logging.info(f"Logging level set to: {LOG_LEVEL}")

class AutoscalerNode:
    def __init__(self, backend_config):
        """Initialize the autoscaler node with backend integration."""
        self.backend_url = backend_config['url']
        self.node_id = backend_config['node_id']
        self.api_key = backend_config['api_key']
        self.node_name = os.getenv("NODE_NAME", f"AutoscalerNode-{socket.gethostname()}")
        self.node_region = os.getenv("NODE_REGION", "us-ashburn-1")
        
        # Convert node_id to int if provided
        if self.node_id:
            try:
                self.node_id = int(self.node_id)
            except ValueError:
                logging.error("NODE_ID must be an integer")
                self.node_id = None
        
        logging.info(f"Backend URL: {self.backend_url}")
        logging.info(f"Node ID: {self.node_id}")
        logging.info(f"API Key: {'***' + self.api_key[-4:] if self.api_key else 'Not set'}")
        
        # Initialize heartbeat service
        if self.node_id and self.api_key:
            self.heartbeat_service = HeartbeatService(self.backend_url, self.node_id, self.api_key)
        else:
            logging.info("No node credentials found. Will attempt auto-registration.")
            self.heartbeat_service = HeartbeatService(self.backend_url, 0, "")
        
        self.heartbeat_thread = None
        self.stop_heartbeat = threading.Event()
        self.pool_analytics = []
        self.config_hash = None
        self.pool_threads = []
        self.stop_all_pools = threading.Event()

    def auto_register(self):
        """Attempt to auto-register this node with the central backend."""
        if self.node_id and self.api_key:
            logging.info(f"Node already has credentials (ID: {self.node_id})")
            return True
            
        logging.info("Attempting auto-registration with central backend...")
        
        # Get local IP address
        try:
            # Connect to a remote server to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "127.0.0.1"
        
        result = self.heartbeat_service.register_node(
            name=self.node_name,
            region=self.node_region,
            ip_address=local_ip,
            description=f"Auto-registered autoscaling node on {socket.gethostname()}"
        )
        
        if result:
            self.node_id = result['node_id']
            self.api_key = result['api_key']
            
            # Save credentials to environment for future runs
            logging.info(f"Registration successful! Node ID: {self.node_id}")
            logging.info("Save these credentials to your config.yaml file:")
            logging.info(f"backend:")
            logging.info(f"  node_id: {self.node_id}")
            logging.info(f"  api_key: \"{self.api_key}\"")
            
            return True
        else:
            logging.error("Auto-registration failed. Please register manually.")
            return False

    def sync_configuration_with_backend(self, local_config_path: str) -> bool:
        """
        Sync configuration with backend. Push local config if backend has none,
        or pull from backend if it has a configuration.
        
        Returns:
            True if sync successful, False otherwise
        """
        if not self.heartbeat_service or not self.node_id or not self.api_key:
            logging.warning("Cannot sync config - missing credentials")
            return False
        
        try:
            # Try to get config from backend
            remote_config = self.heartbeat_service.get_configuration()
            
            if remote_config and remote_config.strip() != "# No configuration set yet":
                # Backend has config, use it
                logging.info("Found configuration on backend, updating local config")
                return self.update_configuration(remote_config, local_config_path)
            else:
                # Backend has no config, push local config
                logging.info("No configuration found on backend, pushing local config")
                with open(local_config_path, 'r') as f:
                    local_config = f.read()
                
                if self.heartbeat_service.push_configuration(local_config):
                    logging.info("Local configuration pushed to backend successfully")
                    return True
                else:
                    logging.error("Failed to push local configuration to backend")
                    return False
                    
        except Exception as e:
            logging.error(f"Failed to sync configuration with backend: {e}")
            return False

    def start_heartbeat(self):
        """Start the heartbeat service in a separate thread."""
        if not self.heartbeat_service or not self.node_id or not self.api_key:
            logging.warning("Cannot start heartbeat - missing credentials")
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
                        logging.info("Configuration update detected from backend")
                        new_config = self.heartbeat_service.get_configuration()
                        if new_config:
                            config_path = os.path.join(
                                os.path.dirname(os.path.dirname(__file__)), "config.yaml"
                            )
                            if self.update_configuration(new_config, config_path):
                                # Restart all pool monitoring with new config
                                self.restart_pool_monitoring()
                    
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

    def update_configuration(self, yaml_config: str, config_path: str) -> bool:
        """Update configuration and restart services if needed."""
        try:
            # Save new configuration
            with open(config_path, 'w') as f:
                f.write(yaml_config)
            
            # Update config hash
            self.config_hash = hashlib.sha256(yaml_config.encode()).hexdigest()
            logging.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update configuration: {e}")
            return False

    def restart_pool_monitoring(self):
        """Restart all pool monitoring threads with new configuration."""
        logging.info("Restarting pool monitoring with updated configuration...")
        
        # Stop all current pool threads
        self.stop_all_pools.set()
        for thread in self.pool_threads:
            if thread.is_alive():
                thread.join(timeout=10)
        
        # Clear thread list and reset stop event
        self.pool_threads = []
        self.stop_all_pools.clear()
        
        # Reload configuration and restart monitoring
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config.yaml"
        )
        try:
            config = load_config(config_path)
            for pool in config["pools"]:
                thread = threading.Thread(target=process_pool, args=(pool, self))
                thread.daemon = True
                thread.start()
                self.pool_threads.append(thread)
            logging.info("Pool monitoring restarted successfully")
        except Exception as e:
            logging.error(f"Failed to restart pool monitoring: {e}")

    def add_pool_analytics(self, pool_id: str, analytics_data: dict):
        """Add pool analytics data to be sent with next heartbeat."""
        self.pool_analytics.append({
            'oracle_pool_id': pool_id,
            # Remove the hardcoded pool_id - let the backend handle it
            **analytics_data
        })

    def shutdown(self):
        """Gracefully shutdown the autoscaler node."""
        logging.info("Shutting down autoscaler node...")
        self.stop_heartbeat_service()
        self.stop_all_pools.set()
        for thread in self.pool_threads:
            if thread.is_alive():
                thread.join(timeout=10)
        logging.info("Autoscaler node shutdown complete")

# ... keep existing code (get_collector function remains unchanged)

def get_collector(pool, compute_management_client, monitoring_client):
    """
    Factory function to get the correct MetricsCollector based on the monitoring method.

    Args:
        pool (dict): Pool configuration details from the YAML file.
        compute_management_client: OCI ComputeManagementClient instance.
        monitoring_client: OCI MonitoringClient instance.

    Returns:
        MetricsCollector instance.
    """
    logging.debug(
        f"Creating collector for pool={pool['instance_pool_id']} "
        f"using compute_management_client={type(compute_management_client)} and monitoring_client={type(monitoring_client)}"
    )
    monitoring_method = pool.get("monitoring_method")
    if monitoring_method == "prometheus":
        return PrometheusMetricsCollector(
            prometheus_url=pool["prometheus_url"],
            compute_management_client=compute_management_client,
            instance_pool_id=pool["instance_pool_id"],
            compartment_id=pool["compartment_id"],
        )
    elif monitoring_method == "oci":
        # Use ComputeManagementClient to fetch instance data
        return OCIMetricsCollector(
            monitoring_client=monitoring_client,
            compute_management_client=compute_management_client,  # Pass both clients
            instance_manager=get_instances_from_instance_pool,
            instance_pool_id=pool["instance_pool_id"],
            compartment_id=pool["compartment_id"],
        )
    else:
        raise ValueError(f"Unknown monitoring method: {monitoring_method}")


def process_pool(pool, autoscaler_node):
    """
    Process a single pool for monitoring and scaling.

    Args:
        pool (dict): Pool configuration details from the YAML file.
        autoscaler_node (AutoscalerNode): The autoscaler node instance.
    """
    region = pool.get("region")
    if not region:
        logging.error(
            f"Region not specified for pool {pool['instance_pool_id']}. Skipping."
        )
        return

    # Build OCI clients for the pool
    try:
        oci_config = build_oci_config(region)
        compute_management_client = ComputeManagementClient(
            oci_config
        )
        monitoring_client = MonitoringClient(
            oci_config
        )
    except Exception as e:
        logging.error(f"Failed to initialize OCI clients for region {region}: {e}")
        raise RuntimeError(f"OCI client initialization failed for region {region}: {e}")

    # Create the appropriate collector
    try:
        collector = get_collector(pool, compute_management_client, monitoring_client)
    except ValueError as ve:
        logging.error(ve)
        raise RuntimeError(
            f"Collector creation failed for pool {pool['instance_pool_id']}: {ve}"
        )

    # Define thresholds
    thresholds = {
        "cpu": pool["cpu_threshold"],
        "ram": pool["ram_threshold"],
    }

    # Define scaling limits
    scaling_limits = pool["scaling_limits"]

    # Initialize and start the Scheduler
    max_instances = scaling_limits["max"]
    schedules = pool.get("schedules", [])  # List of schedule dictionaries
    scheduler_instances = pool.get("scheduler_max_instances", max_instances)

    scheduler = Scheduler(
        compute_management_client=compute_management_client,
        instance_pool_id=pool["instance_pool_id"],
        max_instances=max_instances,
        schedules=schedules,
        scheduler_instances=scheduler_instances
    )
    scheduler.start()

    # function to determine whether the scheduler is active or not
    def scheduler_active_callback():
        return scheduler.is_active()

    # Monitor and scale
    try:
        logging.info(f"Starting monitoring loop for pool: {pool['instance_pool_id']}")
        while not autoscaler_node.stop_all_pools.is_set():
            try:
                # Get metrics before scaling evaluation
                avg_cpu, avg_ram = collector.get_metrics()
                
                # Collect analytics data
                pool_details = collector.compute_management_client.get_instance_pool(
                    instance_pool_id=pool['instance_pool_id']
                ).data
                
                analytics_data = {
                    'current_instances': pool_details.size,
                    'active_instances': pool_details.size,  # Simplified for now
                    'avg_cpu_utilization': avg_cpu,
                    'avg_memory_utilization': avg_ram,
                    'max_cpu_utilization': avg_cpu,  # Simplified
                    'max_memory_utilization': avg_ram,  # Simplified
                    'pool_status': 'healthy',
                    'is_active': True,
                    'scaling_event': None,
                    'scaling_reason': None
                }
                
                # Add analytics to node for heartbeat
                autoscaler_node.add_pool_analytics(pool['instance_pool_id'], analytics_data)
                
                # Pass scaling_limits to evaluate_metrics
                evaluate_metrics(collector, thresholds, scaling_limits, scheduler_active_callback)
                
            except RuntimeError as e:
                logging.error(f"Runtime error in evaluate_metrics: {e}")
                raise  # Re-raise to stop further execution
            
            # Check for stop signal before sleeping
            if autoscaler_node.stop_all_pools.wait(300):  # 5 minutes with early exit
                break
                
    except KeyboardInterrupt:
        logging.info(f"Terminating monitoring for pool: {pool['instance_pool_id']}")
    except Exception as e:
        logging.error(
            f"Error in autoscaling loop for pool {pool['instance_pool_id']}: {e}"
        )
        raise RuntimeError(
            f"Critical failure in autoscaling for pool {pool['instance_pool_id']}: {e}"
        )
    
    finally:
        scheduler.stop()  # Ensure the scheduler stops gracefully when monitoring ends


def main():
    logging.info("Starting autoscaling process...")
    
    # Validate critical environment variables at startup
    webhook_url = os.getenv("WEBHOOK_URL")
    project_name = os.getenv("PROJECT_NAME")
    
    if not webhook_url:
        logging.warning("⚠️  WEBHOOK_URL not set - termination alerts will be disabled")
    else:
        logging.info(f"✓ WEBHOOK_URL configured: {webhook_url[:30]}...")
    
    if not project_name:
        logging.warning("⚠️  PROJECT_NAME not set - webhook alerts will use 'unknown' as project name")
    else:
        logging.info(f"✓ PROJECT_NAME configured: {project_name}")
    
    # Load configuration first to get backend settings
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.yaml"
    )
    logging.debug(f"Loading configuration from: {config_path}")
    
    try:
        config = load_config(config_path)
        backend_config = get_backend_config(config)
        
        # Calculate config hash
        with open(config_path, 'r') as f:
            config_content = f.read()
        config_hash = hashlib.sha256(config_content.encode()).hexdigest()
        
    except Exception as e:
        logging.error(f"Failed to load configuration file: {e}")
        raise RuntimeError(f"Configuration file load failed: {e}")

    # Initialize autoscaler node with backend config from YAML
    autoscaler_node = AutoscalerNode(backend_config)
    autoscaler_node.config_hash = config_hash

    # Set up signal handler for graceful shutdown
    def signal_handler(signum, frame):
        logging.info("Received shutdown signal")
        autoscaler_node.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Attempt auto-registration if needed
    if not autoscaler_node.auto_register():
        logging.error("Failed to register node. Exiting.")
        return

    # Sync configuration with backend
    if not autoscaler_node.sync_configuration_with_backend(config_path):
        logging.warning("Failed to sync configuration with backend, continuing with local config")
    else:
        # Reload config after sync
        config = load_config(config_path)

    # Start heartbeat service
    autoscaler_node.start_heartbeat()

    try:
        # Process each pool from the configuration in separate threads
        for pool in config["pools"]:
            logging.debug(f"Starting processing for pool: {pool}")
            try:
                thread = threading.Thread(target=process_pool, args=(pool, autoscaler_node))
                thread.daemon = True
                thread.start()
                autoscaler_node.pool_threads.append(thread)
            except RuntimeError as re:
                logging.error(f"Error processing pool {pool['instance_pool_id']}: {re}")
                continue  # Skip to the next pool
        
        # Wait for all threads to complete
        for thread in autoscaler_node.pool_threads:
            thread.join()
            
    finally:
        # Stop heartbeat service on exit
        autoscaler_node.shutdown()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        logging.error(f"Runtime error during execution: {e}")
