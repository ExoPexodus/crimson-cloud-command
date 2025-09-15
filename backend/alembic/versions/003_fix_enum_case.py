"""Fix enum case to lowercase

Revision ID: 003
Revises: 002
Create Date: 2025-01-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Check if we need to update any data first
    # Only update if there are uppercase values that need conversion
    try:
        # Try to update role values that are uppercase
        op.execute("""
            UPDATE users 
            SET role = CASE 
                WHEN role::text = 'USER' THEN 'user'::userrole
                WHEN role::text = 'DEVOPS' THEN 'devops'::userrole  
                WHEN role::text = 'ADMIN' THEN 'admin'::userrole
                ELSE role
            END
            WHERE role::text IN ('USER', 'DEVOPS', 'ADMIN')
        """)
        
        # Try to update auth_provider values that are uppercase
        op.execute("""
            UPDATE users 
            SET auth_provider = CASE 
                WHEN auth_provider::text = 'LOCAL' THEN 'local'::authprovider
                WHEN auth_provider::text = 'KEYCLOAK' THEN 'keycloak'::authprovider
                ELSE auth_provider
            END
            WHERE auth_provider::text IN ('LOCAL', 'KEYCLOAK')
        """)
    except Exception:
        # If update fails, the data might already be in correct format
        pass

def downgrade():
    # Revert to uppercase values using explicit CASE mapping
    try:
        op.execute("""
            UPDATE users 
            SET role = CASE 
                WHEN role::text = 'user' THEN 'USER'::userrole
                WHEN role::text = 'devops' THEN 'DEVOPS'::userrole  
                WHEN role::text = 'admin' THEN 'ADMIN'::userrole
                ELSE role
            END
            WHERE role::text IN ('user', 'devops', 'admin')
        """)
        
        op.execute("""
            UPDATE users 
            SET auth_provider = CASE 
                WHEN auth_provider::text = 'local' THEN 'LOCAL'::authprovider
                WHEN auth_provider::text = 'keycloak' THEN 'KEYCLOAK'::authprovider
                ELSE auth_provider
            END
            WHERE auth_provider::text IN ('local', 'keycloak')
        """)
    except Exception:
        # If update fails, data might already be in expected format
        pass