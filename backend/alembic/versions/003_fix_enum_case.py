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
    # Simple approach: Just update the existing data to use lowercase values
    # The enum types in migration 002 already use lowercase values
    op.execute("UPDATE users SET role = LOWER(role) WHERE role != LOWER(role)")
    op.execute("UPDATE users SET auth_provider = LOWER(auth_provider) WHERE auth_provider != LOWER(auth_provider)")

def downgrade():
    # Revert to uppercase values
    op.execute("UPDATE users SET role = UPPER(role)")
    op.execute("UPDATE users SET auth_provider = UPPER(auth_provider)")