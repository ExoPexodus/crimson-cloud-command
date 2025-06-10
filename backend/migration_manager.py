
import logging
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text, inspect
from database import DATABASE_URL, get_db
from models import Base
import os

logger = logging.getLogger(__name__)

def check_table_exists(engine, table_name):
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception:
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
            logger.info("Creating initial migration...")
            command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
            logger.info("Initial migration created")
        
    except Exception as e:
        logger.error(f"Error creating initial migration: {str(e)}")
        raise

def fix_pools_table_schema(engine):
    """Fix the pools table schema if needed"""
    try:
        # Check if pools table exists and has region column
        if check_table_exists(engine, 'pools'):
            if not check_column_exists(engine, 'pools', 'region'):
                logger.info("Adding missing region column to pools table...")
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE pools ADD COLUMN region VARCHAR(100) NOT NULL DEFAULT 'us-ashburn-1'"))
                    conn.commit()
                logger.info("Region column added successfully")
    except Exception as e:
        logger.error(f"Error fixing pools table schema: {str(e)}")
        raise

def initialize_alembic():
    """Initialize Alembic if not already initialized"""
    try:
        alembic_cfg = Config("alembic.ini")
        
        # Check if alembic is initialized
        if not os.path.exists("alembic/versions"):
            logger.info("Initializing Alembic...")
            command.init(alembic_cfg, "alembic")
            logger.info("Alembic initialized successfully")
            
        # Stamp the database with the current revision if no version exists
        try:
            command.current(alembic_cfg)
        except Exception:
            logger.info("Stamping database with head revision...")
            command.stamp(alembic_cfg, "head")
            
    except Exception as e:
        logger.error(f"Error initializing Alembic: {str(e)}")
        # Don't raise here, continue with manual schema fixes

def initialize_database():
    """Initialize database with tables and run migrations"""
    try:
        # Create tables directly first time
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Database connection successful")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Fix schema issues first (fallback)
        fix_pools_table_schema(engine)
        
        # Initialize Alembic if needed
        initialize_alembic()
        
        # Create initial migration if needed
        create_initial_migration()
        
        # Run migrations
        run_migrations()
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
