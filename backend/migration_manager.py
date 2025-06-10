
import logging
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text, inspect
from database import DATABASE_URL, get_db
from models import Base
import os

logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database by dropping all tables and recreating them"""
    try:
        engine = create_engine(DATABASE_URL)
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")
        
        # Drop alembic version table if it exists
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            conn.commit()
        
        logger.info("Database reset completed")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return False

def run_migrations():
    """Run database migrations"""
    try:
        # Create alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise

def create_initial_migration():
    """Create initial migration if it doesn't exist"""
    try:
        alembic_cfg = Config("alembic.ini")
        
        # Check if migrations directory exists
        versions_dir = "alembic/versions"
        if not os.path.exists(versions_dir):
            os.makedirs(versions_dir)
        
        # Check if there are any migration files
        migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and not f.startswith('__')]
        
        if not migration_files:
            logger.info("No migration files found, but we have a pre-created initial migration")
        
    except Exception as e:
        logger.error(f"Error checking initial migration: {str(e)}")
        raise

def check_database_schema():
    """Check if database schema matches our models"""
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Get list of tables
        tables = inspector.get_table_names()
        
        # Expected tables based on our models
        expected_tables = [
            'users', 'nodes', 'pools', 'metrics', 'schedules', 
            'audit_logs', 'node_configurations', 'node_heartbeats', 
            'pool_analytics', 'system_analytics'
        ]
        
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            return False
        
        # Check if pools table has region column (common issue)
        if 'pools' in tables:
            pool_columns = [col['name'] for col in inspector.get_columns('pools')]
            if 'region' not in pool_columns:
                logger.warning("Pools table missing region column")
                return False
        
        logger.info("Database schema appears to be correct")
        return True
        
    except Exception as e:
        logger.error(f"Error checking database schema: {str(e)}")
        return False

def initialize_database(reset_if_needed=False):
    """Initialize database with tables and run migrations"""
    try:
        # Create engine and test connection
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Database connection successful")
        
        # Check if we need to reset the database
        if reset_if_needed or not check_database_schema():
            logger.info("Database schema issues detected, performing reset...")
            reset_database()
        
        # Create initial migration check
        create_initial_migration()
        
        # Run migrations
        run_migrations()
        
        # Verify schema after migration
        if check_database_schema():
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.error("Database schema still has issues after migration")
            return False
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
