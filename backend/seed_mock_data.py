
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
        
        # Create mock nodes
        nodes_data = [
            {
                "name": "Oracle-US-West-Node",
                "region": "us-phoenix-1",
                "ip_address": "10.0.1.100",
                "port": 8080,
                "api_key": "oci_key_us_west_12345",
                "status": NodeStatus.ACTIVE,
                "last_heartbeat": datetime.utcnow(),
                "version": "1.2.3",
                "node_metadata": '{"zone": "AD-1", "shape": "VM.Standard2.1"}'
            },
            {
                "name": "Oracle-US-East-Node",
                "region": "us-ashburn-1",
                "ip_address": "10.0.2.100",
                "port": 8080,
                "api_key": "oci_key_us_east_67890",
                "status": NodeStatus.ACTIVE,
                "last_heartbeat": datetime.utcnow(),
                "version": "1.2.3",
                "node_metadata": '{"zone": "AD-2", "shape": "VM.Standard2.2"}'
            },
            {
                "name": "Oracle-EU-Node",
                "region": "eu-frankfurt-1",
                "ip_address": "10.0.3.100",
                "port": 8080,
                "api_key": "oci_key_eu_central_11111",
                "status": NodeStatus.ACTIVE,
                "last_heartbeat": datetime.utcnow(),
                "version": "1.2.3",
                "node_metadata": '{"zone": "AD-1", "shape": "VM.Standard2.1"}'
            }
        ]
        
        created_nodes = []
        for node_data in nodes_data:
            node = Node(**node_data)
            db.add(node)
            created_nodes.append(node)
        
        db.commit()
        logger.info(f"Created {len(created_nodes)} nodes")
        
        # Create mock pools
        pools_data = [
            {
                "name": "Production API Pool",
                "oracle_pool_id": "ocid1.instancepool.oc1.phx.prod001",
                "compartment_id": "ocid1.compartment.oc1..prod",
                "node_id": created_nodes[0].id,
                "current_instances": 4,
                "min_instances": 2,
                "max_instances": 8,
                "target_instances": 4,
                "status": PoolStatus.HEALTHY,
                "cpu_threshold_scale_up": 75.0,
                "cpu_threshold_scale_down": 25.0,
                "memory_threshold_scale_up": 80.0,
                "memory_threshold_scale_down": 30.0,
            },
            {
                "name": "ML Training Workers",
                "oracle_pool_id": "ocid1.instancepool.oc1.iad.ml001",
                "compartment_id": "ocid1.compartment.oc1..ml",
                "node_id": created_nodes[1].id,
                "current_instances": 6,
                "min_instances": 2,
                "max_instances": 10,
                "target_instances": 6,
                "status": PoolStatus.WARNING,
                "cpu_threshold_scale_up": 70.0,
                "cpu_threshold_scale_down": 20.0,
                "memory_threshold_scale_up": 85.0,
                "memory_threshold_scale_down": 35.0,
            },
            {
                "name": "Database Cluster",
                "oracle_pool_id": "ocid1.instancepool.oc1.fra.db001",
                "compartment_id": "ocid1.compartment.oc1..db",
                "node_id": created_nodes[2].id,
                "current_instances": 3,
                "min_instances": 3,
                "max_instances": 5,
                "target_instances": 3,
                "status": PoolStatus.HEALTHY,
                "cpu_threshold_scale_up": 80.0,
                "cpu_threshold_scale_down": 30.0,
                "memory_threshold_scale_up": 90.0,
                "memory_threshold_scale_down": 40.0,
            },
            {
                "name": "Dev Environment",
                "oracle_pool_id": "ocid1.instancepool.oc1.phx.dev001",
                "compartment_id": "ocid1.compartment.oc1..dev",
                "node_id": created_nodes[0].id,
                "current_instances": 1,
                "min_instances": 0,
                "max_instances": 3,
                "target_instances": 1,
                "status": PoolStatus.INACTIVE,
                "cpu_threshold_scale_up": 70.0,
                "cpu_threshold_scale_down": 20.0,
                "memory_threshold_scale_up": 75.0,
                "memory_threshold_scale_down": 25.0,
            },
            {
                "name": "Test Environment",
                "oracle_pool_id": "ocid1.instancepool.oc1.iad.test001",
                "compartment_id": "ocid1.compartment.oc1..test",
                "node_id": created_nodes[1].id,
                "current_instances": 2,
                "min_instances": 1,
                "max_instances": 4,
                "target_instances": 2,
                "status": PoolStatus.HEALTHY,
                "cpu_threshold_scale_up": 65.0,
                "cpu_threshold_scale_down": 25.0,
                "memory_threshold_scale_up": 70.0,
                "memory_threshold_scale_down": 30.0,
            },
            {
                "name": "Analytics Pool",
                "oracle_pool_id": "ocid1.instancepool.oc1.fra.analytics001",
                "compartment_id": "ocid1.compartment.oc1..analytics",
                "node_id": created_nodes[2].id,
                "current_instances": 0,
                "min_instances": 0,
                "max_instances": 6,
                "target_instances": 0,
                "status": PoolStatus.INACTIVE,
                "cpu_threshold_scale_up": 60.0,
                "cpu_threshold_scale_down": 20.0,
                "memory_threshold_scale_up": 70.0,
                "memory_threshold_scale_down": 25.0,
            }
        ]
        
        created_pools = []
        for pool_data in pools_data:
            pool = Pool(**pool_data)
            db.add(pool)
            created_pools.append(pool)
        
        db.commit()
        logger.info(f"Created {len(created_pools)} pools")
        
        # Create mock metrics for the last 24 hours
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        for i in range(24):  # 24 hours of data
            timestamp = base_time + timedelta(hours=i)
            
            for node in created_nodes:
                # CPU metrics
                cpu_metric = Metric(
                    node_id=node.id,
                    metric_type="cpu",
                    metric_source="oci",
                    value=random.uniform(10, 90),
                    unit="percent",
                    region=node.region,
                    timestamp=timestamp
                )
                db.add(cpu_metric)
                
                # Memory metrics
                memory_metric = Metric(
                    node_id=node.id,
                    metric_type="memory",
                    metric_source="oci",
                    value=random.uniform(20, 85),
                    unit="percent",
                    region=node.region,
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
                    metric_type="instances",
                    metric_source="oci",
                    value=pool.current_instances + random.randint(-1, 2),
                    unit="count",
                    pool_id=pool.oracle_pool_id,
                    region=pool.node.region,
                    timestamp=timestamp
                )
                db.add(instance_metric)
        
        db.commit()
        logger.info("Created metrics for the last 24 hours")
        
        # Create some schedules
        schedules_data = [
            {
                "pool_id": created_pools[0].id,
                "name": "Morning Scale Up",
                "cron_expression": "0 8 * * 1-5",
                "target_instances": 6,
                "is_active": True,
                "description": "Scale up for morning traffic"
            },
            {
                "pool_id": created_pools[0].id,
                "name": "Evening Scale Down",
                "cron_expression": "0 18 * * 1-5",
                "target_instances": 2,
                "is_active": True,
                "description": "Scale down after business hours"
            },
            {
                "pool_id": created_pools[1].id,
                "name": "Weekend ML Training",
                "cron_expression": "0 2 * * 6-7",
                "target_instances": 8,
                "is_active": True,
                "description": "Scale up for weekend ML training jobs"
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
    finally:
        db.close()

if __name__ == "__main__":
    create_mock_data()
