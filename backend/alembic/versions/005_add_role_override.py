"""Add role_override field to users

Revision ID: 005_add_role_override
Revises: 004_enhance_audit_logs
Create Date: 2025-01-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_role_override'
down_revision = '004_enhance_audit_logs'
branch_labels = None
depends_on = None


def upgrade():
    # Add role_override column with default value
    op.add_column('users', sa.Column('role_override', sa.Boolean(), nullable=True, server_default='false'))
    
    # Update existing rows to have role_override = false
    op.execute("UPDATE users SET role_override = false WHERE role_override IS NULL")
    
    # Make the column non-nullable
    op.alter_column('users', 'role_override', nullable=False, server_default=None)


def downgrade():
    op.drop_column('users', 'role_override')
