
"""Initial complete schema for autoscaling system

Revision ID: 001_initial_complete_schema
Revises: 
Create Date: 2025-01-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_complete_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create ENUM types
    node_status_enum = postgresql.ENUM('ACTIVE', 'INACTIVE', 'ERROR', name='nodestatus')
    node_status_enum.create(op.get_bind())
    
    pool_status_enum = postgresql.ENUM('HEALTHY', 'WARNING', 'ERROR', name='poolstatus')
    pool_status_enum.create(op.get_bind())

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create nodes table
    op.create_table('nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', node_status_enum, nullable=True),
        sa.Column('api_key_hash', sa.String(length=64), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_nodes_api_key_hash'), 'nodes', ['api_key_hash'], unique=True)
    op.create_index(op.f('ix_nodes_id'), 'nodes', ['id'], unique=False)

    # Create pools table
    op.create_table('pools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('oracle_pool_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=False),
        sa.Column('min_instances', sa.Integer(), nullable=True),
        sa.Column('max_instances', sa.Integer(), nullable=True),
        sa.Column('current_instances', sa.Integer(), nullable=True),
        sa.Column('status', pool_status_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pools_id'), 'pools', ['id'], unique=False)
    op.create_index(op.f('ix_pools_oracle_pool_id'), 'pools', ['oracle_pool_id'], unique=True)

    # Create metrics table
    op.create_table('metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('pool_id', sa.Integer(), nullable=True),
        sa.Column('metric_type', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metrics_id'), 'metrics', ['id'], unique=False)

    # Create schedules table
    op.create_table('schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('start_time', sa.String(length=5), nullable=False),
        sa.Column('end_time', sa.String(length=5), nullable=False),
        sa.Column('target_instances', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)

    # Create node_configurations table
    op.create_table('node_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('yaml_config', sa.Text(), nullable=False),
        sa.Column('config_hash', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_node_configurations_id'), 'node_configurations', ['id'], unique=False)

    # Create node_heartbeats table
    op.create_table('node_heartbeats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('config_hash', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metrics_data', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_node_heartbeats_id'), 'node_heartbeats', ['id'], unique=False)

    # Create pool_analytics table
    op.create_table('pool_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('oracle_pool_id', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('current_instances', sa.Integer(), nullable=False),
        sa.Column('active_instances', sa.Integer(), nullable=False),
        sa.Column('avg_cpu_utilization', sa.Float(), nullable=False),
        sa.Column('avg_memory_utilization', sa.Float(), nullable=False),
        sa.Column('max_cpu_utilization', sa.Float(), nullable=True),
        sa.Column('max_memory_utilization', sa.Float(), nullable=True),
        sa.Column('pool_status', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('scaling_event', sa.String(length=100), nullable=True),
        sa.Column('scaling_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pool_analytics_id'), 'pool_analytics', ['id'], unique=False)

    # Create system_analytics table
    op.create_table('system_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('total_active_pools', sa.Integer(), nullable=True),
        sa.Column('total_current_instances', sa.Integer(), nullable=True),
        sa.Column('total_active_instances', sa.Integer(), nullable=True),
        sa.Column('avg_system_cpu', sa.Float(), nullable=True),
        sa.Column('avg_system_memory', sa.Float(), nullable=True),
        sa.Column('max_system_cpu', sa.Float(), nullable=True),
        sa.Column('max_system_memory', sa.Float(), nullable=True),
        sa.Column('peak_instances_24h', sa.Integer(), nullable=True),
        sa.Column('max_active_pools_24h', sa.Integer(), nullable=True),
        sa.Column('active_nodes', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_analytics_id'), 'system_analytics', ['id'], unique=False)


def downgrade() -> None:
    # Drop all tables
    op.drop_index(op.f('ix_system_analytics_id'), table_name='system_analytics')
    op.drop_table('system_analytics')
    op.drop_index(op.f('ix_pool_analytics_id'), table_name='pool_analytics')
    op.drop_table('pool_analytics')
    op.drop_index(op.f('ix_node_heartbeats_id'), table_name='node_heartbeats')
    op.drop_table('node_heartbeats')
    op.drop_index(op.f('ix_node_configurations_id'), table_name='node_configurations')
    op.drop_table('node_configurations')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_schedules_id'), table_name='schedules')
    op.drop_table('schedules')
    op.drop_index(op.f('ix_metrics_id'), table_name='metrics')
    op.drop_table('metrics')
    op.drop_index(op.f('ix_pools_oracle_pool_id'), table_name='pools')
    op.drop_index(op.f('ix_pools_id'), table_name='pools')
    op.drop_table('pools')
    op.drop_index(op.f('ix_nodes_id'), table_name='nodes')
    op.drop_index(op.f('ix_nodes_api_key_hash'), table_name='nodes')
    op.drop_table('nodes')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop ENUM types
    sa.Enum(name='poolstatus').drop(op.get_bind())
    sa.Enum(name='nodestatus').drop(op.get_bind())
