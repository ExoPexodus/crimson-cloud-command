"""Add node lifecycle log table

Revision ID: 003
Revises: 002
Create Date: 2025-11-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'node_lifecycle_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('node_id', sa.Integer(), sa.ForeignKey('nodes.id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),  # WENT_OFFLINE, CAME_ONLINE
        sa.Column('previous_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(100), nullable=True),  # heartbeat, manual, system
        sa.Column('extra_data', sa.Text(), nullable=True),  # JSON metadata
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    # Create index for faster queries
    op.create_index('ix_node_lifecycle_logs_node_id', 'node_lifecycle_logs', ['node_id'])
    op.create_index('ix_node_lifecycle_logs_timestamp', 'node_lifecycle_logs', ['timestamp'])
    op.create_index('ix_node_lifecycle_logs_event_type', 'node_lifecycle_logs', ['event_type'])


def downgrade() -> None:
    op.drop_index('ix_node_lifecycle_logs_event_type')
    op.drop_index('ix_node_lifecycle_logs_timestamp')
    op.drop_index('ix_node_lifecycle_logs_node_id')
    op.drop_table('node_lifecycle_logs')
