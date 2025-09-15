"""Convert native enums to varchar for better enum handling

Revision ID: 002_convert_enums_to_varchar
Revises: 001_initial_complete_schema
Create Date: 2025-09-15 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_convert_enums_to_varchar'
down_revision = '001_initial_complete_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Convert users table enums to varchar
    op.add_column('users', sa.Column('role_new', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('auth_provider_new', sa.String(50), nullable=True))
    
    # Copy data from enum columns to new varchar columns
    op.execute("UPDATE users SET role_new = role::text")
    op.execute("UPDATE users SET auth_provider_new = auth_provider::text")
    
    # Drop old enum columns
    op.drop_column('users', 'role')
    op.drop_column('users', 'auth_provider')
    
    # Rename new columns to original names
    op.alter_column('users', 'role_new', new_column_name='role')
    op.alter_column('users', 'auth_provider_new', new_column_name='auth_provider')
    
    # Set defaults and not null constraints
    op.alter_column('users', 'role', server_default='user', nullable=False)
    op.alter_column('users', 'auth_provider', server_default='local', nullable=False)
    
    # Convert nodes table enum to varchar
    op.add_column('nodes', sa.Column('status_new', sa.String(50), nullable=True))
    op.execute("UPDATE nodes SET status_new = status::text")
    op.drop_column('nodes', 'status')
    op.alter_column('nodes', 'status_new', new_column_name='status')
    op.alter_column('nodes', 'status', server_default='inactive')
    
    # Convert pools table enum to varchar
    op.add_column('pools', sa.Column('status_new', sa.String(50), nullable=True))
    op.execute("UPDATE pools SET status_new = status::text")
    op.drop_column('pools', 'status')
    op.alter_column('pools', 'status_new', new_column_name='status')
    op.alter_column('pools', 'status', server_default='healthy')
    
    # Drop unused enum types
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS authprovider") 
    op.execute("DROP TYPE IF EXISTS nodestatus")
    op.execute("DROP TYPE IF EXISTS poolstatus")

def downgrade() -> None:
    # Recreate enum types
    op.execute("CREATE TYPE userrole AS ENUM ('user', 'devops', 'admin')")
    op.execute("CREATE TYPE authprovider AS ENUM ('local', 'keycloak')")
    op.execute("CREATE TYPE nodestatus AS ENUM ('active', 'inactive', 'error')")
    op.execute("CREATE TYPE poolstatus AS ENUM ('healthy', 'warning', 'error')")
    
    # Convert users table varchar back to enums
    op.add_column('users', sa.Column('role_enum', sa.Enum('user', 'devops', 'admin', name='userrole'), nullable=True))
    op.add_column('users', sa.Column('auth_provider_enum', sa.Enum('local', 'keycloak', name='authprovider'), nullable=True))
    
    op.execute("UPDATE users SET role_enum = role::userrole")
    op.execute("UPDATE users SET auth_provider_enum = auth_provider::authprovider")
    
    op.drop_column('users', 'role')
    op.drop_column('users', 'auth_provider')
    
    op.alter_column('users', 'role_enum', new_column_name='role')
    op.alter_column('users', 'auth_provider_enum', new_column_name='auth_provider')
    
    op.alter_column('users', 'role', server_default='user', nullable=False)
    op.alter_column('users', 'auth_provider', server_default='local', nullable=False)
    
    # Convert nodes table varchar back to enum
    op.add_column('nodes', sa.Column('status_enum', sa.Enum('active', 'inactive', 'error', name='nodestatus'), nullable=True))
    op.execute("UPDATE nodes SET status_enum = status::nodestatus")
    op.drop_column('nodes', 'status')
    op.alter_column('nodes', 'status_enum', new_column_name='status')
    op.alter_column('nodes', 'status', server_default='inactive')
    
    # Convert pools table varchar back to enum
    op.add_column('pools', sa.Column('status_enum', sa.Enum('healthy', 'warning', 'error', name='poolstatus'), nullable=True))
    op.execute("UPDATE pools SET status_enum = status::poolstatus")
    op.drop_column('pools', 'status')
    op.alter_column('pools', 'status_enum', new_column_name='status')
    op.alter_column('pools', 'status', server_default='healthy')