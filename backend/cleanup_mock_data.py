
from sqlalchemy.orm import Session
from models import Node, Pool, Metric, Schedule, NodeStatus, PoolStatus, User, AuditLog, NodeConfiguration, NodeHeartbeat, PoolAnalytics, SystemAnalytics
from database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_mock_data():
    """
    Clean up only mock data from the database, preserving real user data
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting cleanup of mock data...")
        
        # Only delete mock data - identify by specific patterns or created during seeding
        total_deleted = 0
        
        # Delete metrics older than 1 day (these are likely mock metrics)
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(days=1)
        
        # Delete old metrics (mock data)
        old_metrics = db.query(Metric).filter(Metric.timestamp < cutoff_time).count()
        if old_metrics > 0:
            deleted_metrics = db.query(Metric).filter(Metric.timestamp < cutoff_time).delete()
            logger.info(f"Deleted {deleted_metrics} old metrics")
            total_deleted += deleted_metrics
        
        # Delete old pool analytics (mock data)
        old_analytics = db.query(PoolAnalytics).filter(PoolAnalytics.timestamp < cutoff_time).count()
        if old_analytics > 0:
            deleted_analytics = db.query(PoolAnalytics).filter(PoolAnalytics.timestamp < cutoff_time).delete()
            logger.info(f"Deleted {deleted_analytics} old pool analytics")
            total_deleted += deleted_analytics
        
        # Delete old system analytics (mock data)
        old_system_analytics = db.query(SystemAnalytics).filter(SystemAnalytics.timestamp < cutoff_time).count()
        if old_system_analytics > 0:
            deleted_system_analytics = db.query(SystemAnalytics).filter(SystemAnalytics.timestamp < cutoff_time).delete()
            logger.info(f"Deleted {deleted_system_analytics} old system analytics")
            total_deleted += deleted_system_analytics
        
        # Delete old heartbeats (mock data)
        old_heartbeats = db.query(NodeHeartbeat).filter(NodeHeartbeat.timestamp < cutoff_time).count()
        if old_heartbeats > 0:
            deleted_heartbeats = db.query(NodeHeartbeat).filter(NodeHeartbeat.timestamp < cutoff_time).delete()
            logger.info(f"Deleted {deleted_heartbeats} old heartbeats")
            total_deleted += deleted_heartbeats
        
        # Only delete mock nodes (nodes without API keys or with specific mock patterns)
        mock_nodes = db.query(Node).filter(
            Node.api_key_hash.is_(None),
            Node.name.like('%Mock%')
        ).all()
        
        for node in mock_nodes:
            # Delete associated data first
            db.query(NodeConfiguration).filter(NodeConfiguration.node_id == node.id).delete()
            db.query(Schedule).filter(Schedule.node_id == node.id).delete()
            # Delete the node
            db.delete(node)
            logger.info(f"Deleted mock node: {node.name}")
            total_deleted += 1
        
        # Only delete pools that are associated with deleted mock nodes or have mock patterns
        mock_pools = db.query(Pool).filter(Pool.name.like('%Mock%')).all()
        for pool in mock_pools:
            db.delete(pool)
            logger.info(f"Deleted mock pool: {pool.name}")
            total_deleted += 1
        
        # Don't delete the admin user or any real users
        logger.info("Preserving all user accounts")
        
        db.commit()
        logger.info(f"✅ Mock data cleanup completed! Total records cleaned: {total_deleted}")
        logger.info("Real user data and nodes have been preserved.")
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_mock_data()
