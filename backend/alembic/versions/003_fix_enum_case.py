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
    # Create new enum types with lowercase values
    new_user_role_enum = sa.Enum('user', 'devops', 'admin', name='userrole_new')
    new_auth_provider_enum = sa.Enum('local', 'keycloak', name='authprovider_new')
    
    new_user_role_enum.create(op.get_bind())
    new_auth_provider_enum.create(op.get_bind())
    
    # Update the role column to use lowercase values
    op.execute("UPDATE users SET role = LOWER(role)")
    op.execute("UPDATE users SET auth_provider = LOWER(auth_provider)")
    
    # Change column types to use new enums
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole_new USING role::text::userrole_new")
    op.execute("ALTER TABLE users ALTER COLUMN auth_provider TYPE authprovider_new USING auth_provider::text::authprovider_new")
    
    # Drop old enum types
    old_user_role_enum = sa.Enum('USER', 'DEVOPS', 'ADMIN', name='userrole')
    old_auth_provider_enum = sa.Enum('LOCAL', 'KEYCLOAK', name='authprovider')
    
    old_user_role_enum.drop(op.get_bind())
    old_auth_provider_enum.drop(op.get_bind())
    
    # Rename new enum types to original names
    op.execute("ALTER TYPE userrole_new RENAME TO userrole")
    op.execute("ALTER TYPE authprovider_new RENAME TO authprovider")

def downgrade():
    # Create old enum types with uppercase values
    old_user_role_enum = sa.Enum('USER', 'DEVOPS', 'ADMIN', name='userrole_old')
    old_auth_provider_enum = sa.Enum('LOCAL', 'KEYCLOAK', name='authprovider_old')
    
    old_user_role_enum.create(op.get_bind())
    old_auth_provider_enum.create(op.get_bind())
    
    # Update values to uppercase
    op.execute("UPDATE users SET role = UPPER(role)")
    op.execute("UPDATE users SET auth_provider = UPPER(auth_provider)")
    
    # Change column types back to uppercase enums
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole_old USING role::text::userrole_old")
    op.execute("ALTER TABLE users ALTER COLUMN auth_provider TYPE authprovider_old USING auth_provider::text::authprovider_old")
    
    # Drop current enum types
    current_user_role_enum = sa.Enum('user', 'devops', 'admin', name='userrole')
    current_auth_provider_enum = sa.Enum('local', 'keycloak', name='authprovider')
    
    current_user_role_enum.drop(op.get_bind())
    current_auth_provider_enum.drop(op.get_bind())
    
    # Rename old enum types back to original names
    op.execute("ALTER TYPE userrole_old RENAME TO userrole")
    op.execute("ALTER TYPE authprovider_old RENAME TO authprovider")