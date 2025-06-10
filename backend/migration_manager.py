
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

def fix_schema_manually(engine):
    """Manual schema fixes as fallback"""
    try:
        with engine.connect() as conn:
            # Add region column to pools if missing
            if check_table_exists(engine, 'pools') and not check_column_exists(engine, 'pools', 'region'):
                logger.info("Adding missing region column to pools table...")
                conn.execute(text("ALTER TABLE pools ADD COLUMN region VARCHAR(100) NOT NULL DEFAULT 'us-ashburn-1'"))
                conn.commit()
                logger.info("Region column added successfully")
            
            # Add current_instances column to pools if missing
            if check_table_exists(engine, 'pools') and not check_column_exists(engine, 'pools', 'current_instances'):
                logger.info("Adding missing current_instances column to pools table...")
                conn.execute(text("ALTER TABLE pools ADD COLUMN current_instances INTEGER NOT NULL DEFAULT 1"))
                conn.commit()
                logger.info("Current_instances column added successfully")
            
            # Add api_key_hash column to nodes if missing
            if check_table_exists(engine, 'nodes') and not check_column_exists(engine, 'nodes', 'api_key_hash'):
                logger.info("Adding missing api_key_hash column to nodes table...")
                conn.execute(text("ALTER TABLE nodes ADD COLUMN api_key_hash VARCHAR(64) UNIQUE"))
                conn.commit()
                logger.info("Api_key_hash column added successfully")
            
            # Add last_heartbeat column to nodes if missing
            if check_table_exists(engine, 'nodes') and not check_column_exists(engine, 'nodes', 'last_heartbeat'):
                logger.info("Adding missing last_heartbeat column to nodes table...")
                conn.execute(text("ALTER TABLE nodes ADD COLUMN last_heartbeat TIMESTAMP"))
                conn.commit()
                logger.info("Last_heartbeat column added successfully")

    except Exception as e:
        logger.error(f"Error fixing schema manually: {str(e)}")

def initialize_alembic():
    """Initialize Alembic if not already initialized"""
    try:
        alembic_cfg = Config("alembic.ini")
        
        # Check if alembic is initialized
        if not os.path.exists("alembic/versions"):
            logger.info("Initializing Alembic...")
            command.init(alembic_cfg, "alembic")
            logger.info("Alembic initialized successfully")
            
        # Check current revision and stamp if needed
        try:
            current = command.current(alembic_cfg)
            if not current:
                logger.info("No current revision found, stamping with head...")
                command.stamp(alembic_cfg, "head")
        except Exception as e:
            logger.warning(f"Could not check current revision: {e}")
            # Try to stamp with head anyway
            try:
                command.stamp(alembic_cfg, "head")
            except Exception as stamp_error:
                logger.warning(f"Could not stamp with head: {stamp_error}")
            
    except Exception as e:
        logger.error(f"Error initializing Alembic: {str(e)}")

def initialize_database():
    """Initialize database with tables and run migrations"""
    try:
        # Create tables directly first time
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Database connection successful")
        
        # Create all tables first (this ensures base structure exists)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Apply manual schema fixes first (fallback)
        fix_schema_manually(engine)
        
        # Initialize Alembic
        initialize_alembic()
        
        # Run migrations to add missing columns and tables
        try:
            run_migrations()
        except Exception as migration_error:
            logger.warning(f"Migration error (continuing with manual fixes): {migration_error}")
            # Continue with manual fixes if migrations fail
            fix_schema_manually(engine)
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
