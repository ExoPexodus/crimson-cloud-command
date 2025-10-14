
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User, UserRole, AuthProvider
import logging

# Set up password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False
)

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
                role=UserRole.ADMIN,
                auth_provider=AuthProvider.LOCAL,
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

def seed_initial_data(db: Session):
    """
    Seed initial data - only creates default admin user
    """
    try:
        # Only ensure admin exists
        admin_created = create_default_admin(db)
        logging.info("Initial data seeding completed - admin user ensured")
        return True
        
    except Exception as e:
        logging.error(f"Error during initial data seeding: {str(e)}")
        return False
