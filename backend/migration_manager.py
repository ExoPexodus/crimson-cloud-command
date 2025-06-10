
import logging
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from database import DATABASE_URL, get_db
from models import Base
import os

logger = logging.getLogger(__name__)

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
        migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
        
        if not migration_files:
            logger.info("Creating initial migration...")
            command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
            logger.info("Initial migration created")
        
    except Exception as e:
        logger.error(f"Error creating initial migration: {str(e)}")
        raise

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
        
        # Create initial migration if needed
        create_initial_migration()
        
        # Run migrations
        run_migrations()
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
