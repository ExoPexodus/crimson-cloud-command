
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User
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
