"""Add offline status to NodeStatus enum

Revision ID: 002_add_offline_status
Revises: 001_initial_complete_schema
Create Date: 2025-11-26 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_offline_status'
down_revision = '001_initial_complete_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add 'OFFLINE' to the nodestatus enum
    op.execute("ALTER TYPE nodestatus ADD VALUE IF NOT EXISTS 'OFFLINE'")

def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # You would need to recreate the enum type if downgrading
    pass
