
import logging
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text, inspect
from database import DATABASE_URL, get_db
from models import Base
import os

logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database by dropping all tables and recreating them - USE WITH CAUTION"""
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

def has_existing_data():
    """Check if database has existing user data - only after tables exist"""
    try:
        # First check if basic tables exist
        if not check_database_schema():
            return False
            
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check if we have any real nodes (with API keys)
            result = conn.execute(text("SELECT COUNT(*) FROM nodes WHERE api_key_hash IS NOT NULL"))
            node_count = result.scalar()
            
            # Check if we have any users besides the default admin
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE email != 'admin@admin.com'"))
            user_count = result.scalar()
            
            return node_count > 0 or user_count > 0
    except Exception as e:
        logger.error(f"Error checking existing data: {str(e)}")
        return False

def initialize_database(force_reset=False):
    """Initialize database with tables and run migrations - preserves existing data unless force_reset=True"""
    try:
        # Create engine and test connection
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Database connection successful")
        
        # Check if schema exists first
        schema_exists = check_database_schema()
        
        if not schema_exists:
            logger.info("Database schema missing, initializing...")
            
            # Try migrations first for a clean setup
            if run_migrations():
                logger.info("Database initialized successfully via migrations")
            else:
                logger.info("Migration failed, creating tables directly...")
                if create_tables_directly():
                    logger.info("Tables created directly, stamping with migration version...")
                    stamp_database()
                else:
                    logger.error("Failed to create database schema")
                    return False
        else:
            logger.info("Database schema exists")
            
            # Check if we should preserve existing data
            has_data = has_existing_data()
            
            if force_reset and has_data:
                logger.warning("Force reset requested - will lose existing data!")
                reset_database()
                
                # Recreate schema
                if run_migrations():
                    logger.info("Database reset and reinitialized via migrations")
                else:
                    create_tables_directly()
                    stamp_database()
                    logger.info("Database reset and reinitialized directly")
            elif has_data:
                logger.info("Existing data detected, preserving it")
                # Just run migrations to update schema if needed
                if not run_migrations():
                    logger.warning("Migration failed, but database seems to be working")
            else:
                logger.info("No existing data detected")
                # Run migrations to ensure schema is up to date
                if not run_migrations():
                    logger.warning("Migration failed, but proceeding")
        
        # Final verification
        if check_database_schema():
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.warning("Database schema still has issues, but proceeding")
            return True  # Don't fail completely
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
