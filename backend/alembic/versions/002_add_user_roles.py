"""Add user roles and auth provider

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001_initial_complete_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum types
    user_role_enum = sa.Enum('USER', 'DEVOPS', 'ADMIN', name='userrole')
    auth_provider_enum = sa.Enum('LOCAL', 'KEYCLOAK', name='authprovider')
    
    user_role_enum.create(op.get_bind())
    auth_provider_enum.create(op.get_bind())
    
    # Add new columns to users table
    op.add_column('users', sa.Column('role', user_role_enum, nullable=False, server_default='USER'))
    op.add_column('users', sa.Column('auth_provider', auth_provider_enum, nullable=False, server_default='LOCAL'))
    op.add_column('users', sa.Column('keycloak_user_id', sa.String(255), nullable=True))
    
    # Make hashed_password nullable for Keycloak users
    op.alter_column('users', 'hashed_password', nullable=True)
    
    # Add indexes
    op.create_index('ix_users_keycloak_user_id', 'users', ['keycloak_user_id'], unique=True)
    
    # Update existing admin user to have admin role
    op.execute("UPDATE users SET role = 'ADMIN' WHERE email = 'admin@admin.com'")

def downgrade():
    # Remove indexes
    op.drop_index('ix_users_keycloak_user_id', 'users')
    
    # Remove columns
    op.drop_column('users', 'keycloak_user_id')
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'role')
    
    # Make hashed_password non-nullable again
    op.alter_column('users', 'hashed_password', nullable=False)
    
    # Drop enum types
    user_role_enum = sa.Enum('USER', 'DEVOPS', 'ADMIN', name='userrole')
    auth_provider_enum = sa.Enum('LOCAL', 'KEYCLOAK', name='authprovider')
    
    user_role_enum.drop(op.get_bind())
    auth_provider_enum.drop(op.get_bind())