
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

def create_tables_directly():
    """Create tables directly using SQLAlchemy metadata"""
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully using SQLAlchemy")
        return True
    except Exception as e:
        logger.error(f"Error creating tables directly: {str(e)}")
        return False

def run_migrations():
    """Run database migrations"""
    try:
        # Check if alembic.ini exists
        if not os.path.exists("alembic.ini"):
            logger.error("alembic.ini not found")
            return False
            
        # Create alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        return False

def stamp_database():
    """Stamp the database with the current migration version"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        logger.info("Database stamped successfully")
        return True
    except Exception as e:
        logger.error(f"Error stamping database: {str(e)}")
        return False

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
            
            # Reset database completely
            reset_database()
            
            # Try creating tables directly first
            if create_tables_directly():
                logger.info("Tables created directly, stamping with migration version...")
                stamp_database()
            else:
                # Fallback to migrations
                logger.info("Direct table creation failed, trying migrations...")
                if not run_migrations():
                    logger.error("Migration failed, creating tables directly as fallback...")
                    create_tables_directly()
                    stamp_database()
        else:
            logger.info("Database schema is correct, skipping reset")
        
        # Final verification
        if check_database_schema():
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.error("Database schema still has issues after initialization")
            return False
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
