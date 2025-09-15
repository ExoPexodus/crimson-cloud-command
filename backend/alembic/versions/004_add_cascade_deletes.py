"""Add cascade deletes for node relationships

Revision ID: 004
Revises: 003
Create Date: 2025-01-11 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing foreign key constraints and recreate with CASCADE
    
    # pools.node_id -> nodes.id (CASCADE DELETE)
    op.drop_constraint('pools_node_id_fkey', 'pools', type_='foreignkey')
    op.create_foreign_key('pools_node_id_fkey', 'pools', 'nodes', ['node_id'], ['id'], ondelete='CASCADE')
    
    # metrics.node_id -> nodes.id (CASCADE DELETE)
    op.drop_constraint('metrics_node_id_fkey', 'metrics', type_='foreignkey')
    op.create_foreign_key('metrics_node_id_fkey', 'metrics', 'nodes', ['node_id'], ['id'], ondelete='CASCADE')
    
    # schedules.node_id -> nodes.id (CASCADE DELETE)
    op.drop_constraint('schedules_node_id_fkey', 'schedules', type_='foreignkey')
    op.create_foreign_key('schedules_node_id_fkey', 'schedules', 'nodes', ['node_id'], ['id'], ondelete='CASCADE')
    
    # node_configurations.node_id -> nodes.id (CASCADE DELETE)
    op.drop_constraint('node_configurations_node_id_fkey', 'node_configurations', type_='foreignkey')
    op.create_foreign_key('node_configurations_node_id_fkey', 'node_configurations', 'nodes', ['node_id'], ['id'], ondelete='CASCADE')
    
    # node_heartbeats.node_id -> nodes.id (CASCADE DELETE)
    op.drop_constraint('node_heartbeats_node_id_fkey', 'node_heartbeats', type_='foreignkey')
    op.create_foreign_key('node_heartbeats_node_id_fkey', 'node_heartbeats', 'nodes', ['node_id'], ['id'], ondelete='CASCADE')
    
    # pool_analytics.node_id -> nodes.id (CASCADE DELETE)
    op.drop_constraint('pool_analytics_node_id_fkey', 'pool_analytics', type_='foreignkey')
    op.create_foreign_key('pool_analytics_node_id_fkey', 'pool_analytics', 'nodes', ['node_id'], ['id'], ondelete='CASCADE')

def downgrade():
    # Revert back to original foreign key constraints (without CASCADE)
    
    # pools.node_id -> nodes.id
    op.drop_constraint('pools_node_id_fkey', 'pools', type_='foreignkey')
    op.create_foreign_key('pools_node_id_fkey', 'pools', 'nodes', ['node_id'], ['id'])
    
    # metrics.node_id -> nodes.id
    op.drop_constraint('metrics_node_id_fkey', 'metrics', type_='foreignkey')
    op.create_foreign_key('metrics_node_id_fkey', 'metrics', 'nodes', ['node_id'], ['id'])
    
    # schedules.node_id -> nodes.id
    op.drop_constraint('schedules_node_id_fkey', 'schedules', type_='foreignkey')
    op.create_foreign_key('schedules_node_id_fkey', 'schedules', 'nodes', ['node_id'], ['id'])
    
    # node_configurations.node_id -> nodes.id
    op.drop_constraint('node_configurations_node_id_fkey', 'node_configurations', type_='foreignkey')
    op.create_foreign_key('node_configurations_node_id_fkey', 'node_configurations', 'nodes', ['node_id'], ['id'])
    
    # node_heartbeats.node_id -> nodes.id
    op.drop_constraint('node_heartbeats_node_id_fkey', 'node_heartbeats', type_='foreignkey')
    op.create_foreign_key('node_heartbeats_node_id_fkey', 'node_heartbeats', 'nodes', ['node_id'], ['id'])
    
    # pool_analytics.node_id -> nodes.id
    op.drop_constraint('pool_analytics_node_id_fkey', 'pool_analytics', type_='foreignkey')
    op.create_foreign_key('pool_analytics_node_id_fkey', 'pool_analytics', 'nodes', ['node_id'], ['id'])