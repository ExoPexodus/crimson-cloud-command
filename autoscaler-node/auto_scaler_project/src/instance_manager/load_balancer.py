
"""
Load balancer module for managing instance pool load distribution.
This module provides functionality to monitor and balance load across instances.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LoadBalancer:
    """Load balancer for managing instance pool traffic distribution"""
    
    def __init__(self, pool_id: str):
        self.pool_id = pool_id
        self.instances: List[Dict[str, Any]] = []
        self.load_metrics: Dict[str, float] = {}
        
    def add_instance(self, instance_id: str, instance_data: Dict[str, Any]) -> None:
        """Add an instance to the load balancer"""
        instance_info = {
            "id": instance_id,
            "data": instance_data,
            "added_at": datetime.utcnow(),
            "status": "active"
        }
        self.instances.append(instance_info)
        logger.info(f"Added instance {instance_id} to load balancer for pool {self.pool_id}")
    
    def remove_instance(self, instance_id: str) -> bool:
        """Remove an instance from the load balancer"""
        for i, instance in enumerate(self.instances):
            if instance["id"] == instance_id:
                self.instances.pop(i)
                logger.info(f"Removed instance {instance_id} from load balancer for pool {self.pool_id}")
                return True
        return False
    
    def update_load_metrics(self, instance_id: str, cpu_usage: float, memory_usage: float) -> None:
        """Update load metrics for an instance"""
        load_score = (cpu_usage + memory_usage) / 2
        self.load_metrics[instance_id] = load_score
        logger.debug(f"Updated load metrics for instance {instance_id}: {load_score}")
    
    def get_least_loaded_instance(self) -> Optional[str]:
        """Get the instance with the lowest load"""
        if not self.load_metrics:
            return None
        
        least_loaded = min(self.load_metrics.items(), key=lambda x: x[1])
        return least_loaded[0]
    
    def get_load_distribution(self) -> Dict[str, float]:
        """Get current load distribution across instances"""
        return self.load_metrics.copy()
    
    def is_balanced(self, threshold: float = 20.0) -> bool:
        """Check if load is balanced across instances"""
        if len(self.load_metrics) < 2:
            return True
        
        loads = list(self.load_metrics.values())
        max_load = max(loads)
        min_load = min(loads)
        
        return (max_load - min_load) <= threshold
    
    def get_rebalancing_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for rebalancing load"""
        recommendations = []
        
        if not self.is_balanced():
            least_loaded = self.get_least_loaded_instance()
            most_loaded = max(self.load_metrics.items(), key=lambda x: x[1])
            
            recommendations.append({
                "action": "redirect_traffic",
                "from_instance": most_loaded[0],
                "to_instance": least_loaded,
                "reason": f"Load imbalance detected: {most_loaded[1]:.2f} vs {self.load_metrics[least_loaded]:.2f}"
            })
        
        return recommendations
