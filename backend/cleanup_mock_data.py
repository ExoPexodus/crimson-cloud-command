
from sqlalchemy.orm import Session
from models import Node, Pool, Metric, Schedule, NodeStatus, PoolStatus, User, AuditLog, NodeConfiguration, NodeHeartbeat, PoolAnalytics, SystemAnalytics
from database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_mock_data():
    """
    Clean up all mock data from the database
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting cleanup of mock data...")
        
        # Delete all records in dependency order (foreign keys first)
        tables_to_clean = [
            (Metric, "metrics"),
            (Schedule, "schedules"),
            (NodeConfiguration, "node_configurations"),
            (NodeHeartbeat, "node_heartbeats"),
            (PoolAnalytics, "pool_analytics"),
            (SystemAnalytics, "system_analytics"),
            (AuditLog, "audit_logs"),
            (Pool, "pools"),
            (Node, "nodes")
        ]
        
        total_deleted = 0
        
        for model, table_name in tables_to_clean:
            count = db.query(model).count()
            if count > 0:
                deleted = db.query(model).delete()
                logger.info(f"Deleted {deleted} records from {table_name}")
                total_deleted += deleted
            else:
                logger.info(f"No records found in {table_name}")
        
        # Keep the admin user - only delete if you want to remove it too
        # Uncomment the next lines if you want to delete the admin user as well
        # admin_count = db.query(User).count()
        # if admin_count > 0:
        #     deleted_users = db.query(User).delete()
        #     logger.info(f"Deleted {deleted_users} admin users")
        #     total_deleted += deleted_users
        
        db.commit()
        logger.info(f"✅ Cleanup completed successfully! Total records deleted: {total_deleted}")
        logger.info("Database is now clean and ready for production use.")
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_mock_data()
