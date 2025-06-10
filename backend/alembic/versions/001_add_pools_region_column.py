
"""Add region column to pools table

Revision ID: 001_add_pools_region_column
Revises: 
Create Date: 2025-06-10 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_add_pools_region_column'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Check if the column already exists before adding it
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='pools' AND column_name='region'
    """))
    
    if not result.fetchone():
        op.add_column('pools', sa.Column('region', sa.String(100), nullable=False, server_default='us-ashburn-1'))

def downgrade() -> None:
    op.drop_column('pools', 'region')
