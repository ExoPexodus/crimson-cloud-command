
import requests
import logging
import time
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class HeartbeatService:
    def __init__(self, backend_url: str, node_id: int, api_key: str):
        """
        Initialize heartbeat service for communication with central backend.
        
        Args:
            backend_url: URL of the central backend API
            node_id: ID of this autoscaling node
            api_key: API key for authentication
        """
        self.backend_url = backend_url.rstrip('/')
        self.node_id = node_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,  # Use X-API-Key header instead of Bearer
            'Content-Type': 'application/json'
        })
        
    def send_heartbeat(self, status: str = "active", error_message: str = None, 
                      pool_analytics: List[Dict] = None, config_hash: str = None) -> Dict[str, Any]:
        """
        Send heartbeat to central backend with current status and metrics.
        
        Args:
            status: Current node status
            error_message: Error message if any
            pool_analytics: List of pool analytics data
            config_hash: Current configuration hash
            
        Returns:
            Response from backend
        """
        try:
            heartbeat_data = {
                'status': status,
                'error_message': error_message,
                'config_hash': config_hash,
                'pool_analytics': pool_analytics or [],
                'metrics_data': self._collect_system_metrics()
            }
            
            # Use the correct endpoint path that matches backend main.py
            url = f"{self.backend_url}/heartbeat"
            response = self.session.post(url, json=heartbeat_data, timeout=30)
            
            if response.status_code == 200:
                logging.info(f"Heartbeat sent successfully to {url}")
                return response.json()
            else:
                logging.error(f"Heartbeat failed: {response.status_code} - {response.text}")
                return {'error': f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send heartbeat: {e}")
            return {'error': str(e)}
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect basic system metrics for heartbeat."""
        try:
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'timestamp': datetime.utcnow().isoformat()
            }
        except ImportError:
            # psutil not available, return basic info
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'metrics_unavailable'
            }
    
    def get_configuration(self) -> Optional[str]:
        """
        Fetch latest configuration from central backend.
        
        Returns:
            YAML configuration string or None if failed
        """
        try:
            url = f"{self.backend_url}/nodes/{self.node_id}/config"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                config_data = response.json()
                logging.info("Configuration fetched successfully")
                return config_data.get('yaml_config')
            else:
                logging.error(f"Failed to fetch config: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch configuration: {e}")
            return None
    
    def send_pool_analytics(self, pool_analytics: List[Dict]) -> bool:
        """
        Send pool analytics data to central backend.
        
        Args:
            pool_analytics: List of pool analytics data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.send_heartbeat(
                status="active",
                pool_analytics=pool_analytics
            )
            return 'error' not in response
        except Exception as e:
            logging.error(f"Failed to send pool analytics: {e}")
            return False
