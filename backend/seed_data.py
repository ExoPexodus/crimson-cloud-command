
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User, Node
import logging

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_default_admin(db: Session):
    """
    Create a default admin user if it doesn't exist
    """
    # Default admin credentials
    DEFAULT_ADMIN_EMAIL = "admin@admin.com"
    DEFAULT_ADMIN_PASSWORD = "admin"
    DEFAULT_ADMIN_NAME = "Admin User"
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first()
        
        if not existing_admin:
            logging.info("Creating default admin user...")
            hashed_password = pwd_context.hash(DEFAULT_ADMIN_PASSWORD)
            
            # Create default admin user
            default_admin = User(
                email=DEFAULT_ADMIN_EMAIL,
                hashed_password=hashed_password,
                full_name=DEFAULT_ADMIN_NAME,
                is_active=True
            )
            
            db.add(default_admin)
            db.commit()
            logging.info(f"Default admin user created with email: {DEFAULT_ADMIN_EMAIL}")
            return True
        else:
            logging.info(f"Default admin user already exists: {DEFAULT_ADMIN_EMAIL}")
            return False
            
    except Exception as e:
        logging.error(f"Error creating default admin user: {str(e)}")
        db.rollback()
        return False

def should_seed_mock_data(db: Session):
    """
    Check if we should seed mock data (only if no real nodes exist)
    """
    try:
        # Check if we have any nodes with API keys (real nodes)
        real_nodes = db.query(Node).filter(Node.api_key_hash.isnot(None)).count()
        
        # Check if we have any nodes at all
        total_nodes = db.query(Node).count()
        
        # Only seed if we have no real nodes and less than 3 total nodes
        return real_nodes == 0 and total_nodes < 3
        
    except Exception as e:
        logging.error(f"Error checking if should seed mock data: {str(e)}")
        return False

def seed_initial_data(db: Session):
    """
    Seed initial data only if needed
    """
    try:
        # Always ensure admin exists
        admin_created = create_default_admin(db)
        
        # Only seed mock data if we don't have real data
        if should_seed_mock_data(db):
            logging.info("No real nodes detected, seeding mock data for demonstration...")
            try:
                from seed_mock_data import create_mock_data
                create_mock_data()
                logging.info("Mock data seeded successfully")
            except Exception as e:
                logging.error(f"Failed to seed mock data: {str(e)}")
        else:
            logging.info("Real nodes detected or sufficient data exists, skipping mock data seeding")
        
        return True
        
    except Exception as e:
        logging.error(f"Error during initial data seeding: {str(e)}")
        return False
