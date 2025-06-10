
from sqlalchemy.orm import Session
from models import Node, Pool, Metric, Schedule, NodeStatus, PoolStatus
from database import SessionLocal
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_data():
    """
    Create comprehensive mock data for testing
    """
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - remove in production)
        db.query(Metric).delete()
        db.query(Schedule).delete()
        db.query(Pool).delete()
        db.query(Node).delete()
        db.commit()
        
        # Create mock nodes - using only valid Node model fields
        nodes_data = [
            {
                "name": "Oracle-US-West-Node",
                "region": "us-phoenix-1",
                "ip_address": "10.0.1.100",
                "description": "Primary Oracle node in US West region",
                "status": NodeStatus.ACTIVE,
                "last_heartbeat": datetime.utcnow()
            },
            {
                "name": "Oracle-US-East-Node", 
                "region": "us-ashburn-1",
                "ip_address": "10.0.2.100",
                "description": "Primary Oracle node in US East region",
                "status": NodeStatus.ACTIVE,
                "last_heartbeat": datetime.utcnow()
            },
            {
                "name": "Oracle-EU-Node",
                "region": "eu-frankfurt-1", 
                "ip_address": "10.0.3.100",
                "description": "Primary Oracle node in EU region",
                "status": NodeStatus.ACTIVE,
                "last_heartbeat": datetime.utcnow()
            }
        ]
        
        created_nodes = []
        for node_data in nodes_data:
            node = Node(**node_data)
            db.add(node)
            created_nodes.append(node)
        
        db.commit()
        logger.info(f"Created {len(created_nodes)} nodes")
        
        # Create mock pools - using only valid Pool model fields
        pools_data = [
            {
                "name": "Production API Pool",
                "oracle_pool_id": "ocid1.instancepool.oc1.phx.prod001",
                "node_id": created_nodes[0].id,
                "region": "us-phoenix-1",
                "current_instances": 4,
                "min_instances": 2,
                "max_instances": 8,
                "status": PoolStatus.HEALTHY
            },
            {
                "name": "ML Training Workers",
                "oracle_pool_id": "ocid1.instancepool.oc1.iad.ml001", 
                "node_id": created_nodes[1].id,
                "region": "us-ashburn-1",
                "current_instances": 6,
                "min_instances": 2,
                "max_instances": 10,
                "status": PoolStatus.WARNING
            },
            {
                "name": "Database Cluster",
                "oracle_pool_id": "ocid1.instancepool.oc1.fra.db001",
                "node_id": created_nodes[2].id,
                "region": "eu-frankfurt-1",
                "current_instances": 3,
                "min_instances": 3,
                "max_instances": 5,
                "status": PoolStatus.HEALTHY
            },
            {
                "name": "Dev Environment", 
                "oracle_pool_id": "ocid1.instancepool.oc1.phx.dev001",
                "node_id": created_nodes[0].id,
                "region": "us-phoenix-1",
                "current_instances": 1,
                "min_instances": 0,
                "max_instances": 3,
                "status": PoolStatus.HEALTHY
            },
            {
                "name": "Test Environment",
                "oracle_pool_id": "ocid1.instancepool.oc1.iad.test001",
                "node_id": created_nodes[1].id,
                "region": "us-ashburn-1", 
                "current_instances": 2,
                "min_instances": 1,
                "max_instances": 4,
                "status": PoolStatus.HEALTHY
            },
            {
                "name": "Analytics Pool",
                "oracle_pool_id": "ocid1.instancepool.oc1.fra.analytics001",
                "node_id": created_nodes[2].id,
                "region": "eu-frankfurt-1",
                "current_instances": 0,
                "min_instances": 0,
                "max_instances": 6,
                "status": PoolStatus.HEALTHY
            }
        ]
        
        created_pools = []
        for pool_data in pools_data:
            pool = Pool(**pool_data)
            db.add(pool)
            created_pools.append(pool)
        
        db.commit()
        logger.info(f"Created {len(created_pools)} pools")
        
        # Create mock metrics for the last 24 hours - using only valid Metric model fields
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        for i in range(24):  # 24 hours of data
            timestamp = base_time + timedelta(hours=i)
            
            for node in created_nodes:
                # CPU metrics
                cpu_metric = Metric(
                    node_id=node.id,
                    metric_type="cpu",
                    value=random.uniform(10, 90),
                    unit="percent",
                    timestamp=timestamp
                )
                db.add(cpu_metric)
                
                # Memory metrics
                memory_metric = Metric(
                    node_id=node.id,
                    metric_type="memory", 
                    value=random.uniform(20, 85),
                    unit="percent",
                    timestamp=timestamp
                )
                db.add(memory_metric)
        
        # Create pool-specific metrics
        for pool in created_pools:
            for i in range(24):
                timestamp = base_time + timedelta(hours=i)
                
                # Instance count metrics
                instance_metric = Metric(
                    node_id=pool.node_id,
                    pool_id=pool.id,
                    metric_type="instances",
                    value=pool.current_instances + random.randint(-1, 2),
                    unit="count",
                    timestamp=timestamp
                )
                db.add(instance_metric)
        
        db.commit()
        logger.info("Created metrics for the last 24 hours")
        
        # Create some schedules - using only valid Schedule model fields  
        schedules_data = [
            {
                "node_id": created_nodes[0].id,
                "name": "Morning Scale Up",
                "start_time": "08:00",
                "end_time": "18:00", 
                "target_instances": 6,
                "is_active": True
            },
            {
                "node_id": created_nodes[0].id,
                "name": "Evening Scale Down",
                "start_time": "18:00",
                "end_time": "08:00",
                "target_instances": 2,
                "is_active": True
            },
            {
                "node_id": created_nodes[1].id,
                "name": "Weekend ML Training",
                "start_time": "02:00", 
                "end_time": "10:00",
                "target_instances": 8,
                "is_active": True
            }
        ]
        
        for schedule_data in schedules_data:
            schedule = Schedule(**schedule_data)
            db.add(schedule)
        
        db.commit()
        logger.info(f"Created {len(schedules_data)} schedules")
        
        logger.info("Mock data creation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error creating mock data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_mock_data()
