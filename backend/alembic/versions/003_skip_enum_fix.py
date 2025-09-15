"""Skip enum case fix - not needed

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
    # Skip - enum values should already be correct from migration 002
    pass

def downgrade():
    # Skip - nothing to revert
    pass