
"""Fix complete database schema

Revision ID: 002_fix_complete_schema
Revises: 001_add_pools_region_column
Create Date: 2025-06-10 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_fix_complete_schema'
down_revision = '001_add_pools_region_column'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Check and add missing columns to nodes table
    conn = op.get_bind()
    
    # Check if api_key_hash column exists in nodes table
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nodes' AND column_name='api_key_hash'
    """))
    if not result.fetchone():
        op.add_column('nodes', sa.Column('api_key_hash', sa.String(64), nullable=True, unique=True))
    
    # Check if last_heartbeat column exists in nodes table
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nodes' AND column_name='last_heartbeat'
    """))
    if not result.fetchone():
        op.add_column('nodes', sa.Column('last_heartbeat', sa.DateTime, nullable=True))
    
    # Check if ip_address column exists in nodes table
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nodes' AND column_name='ip_address'
    """))
    if not result.fetchone():
        op.add_column('nodes', sa.Column('ip_address', sa.String(45), nullable=True))
    
    # Check if description column exists in nodes table
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nodes' AND column_name='description'
    """))
    if not result.fetchone():
        op.add_column('nodes', sa.Column('description', sa.Text, nullable=True))
    
    # Check if status column exists in nodes table
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='nodes' AND column_name='status'
    """))
    if not result.fetchone():
        # Create enum type for node status if it doesn't exist
        try:
            op.execute("CREATE TYPE nodestatus AS ENUM ('active', 'inactive', 'error')")
        except:
            pass  # Type might already exist
        op.add_column('nodes', sa.Column('status', sa.Enum('active', 'inactive', 'error', name='nodestatus'), nullable=True, server_default='inactive'))
    
    # Check if current_instances column exists in pools table
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='pools' AND column_name='current_instances'
    """))
    if not result.fetchone():
        op.add_column('pools', sa.Column('current_instances', sa.Integer, nullable=False, server_default='1'))
    
    # Check if status column exists in pools table
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='pools' AND column_name='status'
    """))
    if not result.fetchone():
        # Create enum type for pool status if it doesn't exist
        try:
            op.execute("CREATE TYPE poolstatus AS ENUM ('healthy', 'warning', 'error')")
        except:
            pass  # Type might already exist
        op.add_column('pools', sa.Column('status', sa.Enum('healthy', 'warning', 'error', name='poolstatus'), nullable=True, server_default='healthy'))
    
    # Create node_configurations table if it doesn't exist
    try:
        op.create_table('node_configurations',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('node_id', sa.Integer, sa.ForeignKey('nodes.id'), nullable=False),
            sa.Column('yaml_config', sa.Text, nullable=False),
            sa.Column('config_hash', sa.String(64), nullable=False),
            sa.Column('is_active', sa.Boolean, default=True),
            sa.Column('created_at', sa.DateTime, default=sa.func.now())
        )
    except:
        pass  # Table might already exist
    
    # Create node_heartbeats table if it doesn't exist
    try:
        op.create_table('node_heartbeats',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('node_id', sa.Integer, sa.ForeignKey('nodes.id'), nullable=False),
            sa.Column('config_hash', sa.String(64), nullable=True),
            sa.Column('status', sa.String(50), nullable=False),
            sa.Column('error_message', sa.Text, nullable=True),
            sa.Column('metrics_data', sa.Text, nullable=True),
            sa.Column('timestamp', sa.DateTime, default=sa.func.now())
        )
    except:
        pass  # Table might already exist
    
    # Create pool_analytics table if it doesn't exist
    try:
        op.create_table('pool_analytics',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('pool_id', sa.Integer, sa.ForeignKey('pools.id'), nullable=False),
            sa.Column('node_id', sa.Integer, sa.ForeignKey('nodes.id'), nullable=False),
            sa.Column('oracle_pool_id', sa.String(255), nullable=False),
            sa.Column('timestamp', sa.DateTime, default=sa.func.now()),
            sa.Column('current_instances', sa.Integer, nullable=False),
            sa.Column('active_instances', sa.Integer, nullable=False),
            sa.Column('avg_cpu_utilization', sa.Float, nullable=False),
            sa.Column('avg_memory_utilization', sa.Float, nullable=False),
            sa.Column('max_cpu_utilization', sa.Float, nullable=True),
            sa.Column('max_memory_utilization', sa.Float, nullable=True),
            sa.Column('pool_status', sa.String(50), default='healthy'),
            sa.Column('is_active', sa.Boolean, default=True),
            sa.Column('scaling_event', sa.String(100), nullable=True),
            sa.Column('scaling_reason', sa.Text, nullable=True)
        )
    except:
        pass  # Table might already exist
    
    # Create system_analytics table if it doesn't exist
    try:
        op.create_table('system_analytics',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('timestamp', sa.DateTime, default=sa.func.now()),
            sa.Column('total_active_pools', sa.Integer, default=0),
            sa.Column('total_current_instances', sa.Integer, default=0),
            sa.Column('total_active_instances', sa.Integer, default=0),
            sa.Column('avg_system_cpu', sa.Float, default=0.0),
            sa.Column('avg_system_memory', sa.Float, default=0.0),
            sa.Column('max_system_cpu', sa.Float, default=0.0),
            sa.Column('max_system_memory', sa.Float, default=0.0),
            sa.Column('peak_instances_24h', sa.Integer, default=0),
            sa.Column('max_active_pools_24h', sa.Integer, default=0),
            sa.Column('active_nodes', sa.Integer, default=0)
        )
    except:
        pass  # Table might already exist
    
    # Create audit_logs table if it doesn't exist
    try:
        op.create_table('audit_logs',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
            sa.Column('action', sa.String(255), nullable=False),
            sa.Column('resource_type', sa.String(100), nullable=False),
            sa.Column('resource_id', sa.Integer, nullable=True),
            sa.Column('details', sa.Text, nullable=True),
            sa.Column('timestamp', sa.DateTime, default=sa.func.now())
        )
    except:
        pass  # Table might already exist

def downgrade() -> None:
    # Remove added columns
    op.drop_column('nodes', 'api_key_hash')
    op.drop_column('nodes', 'last_heartbeat')
    op.drop_column('nodes', 'ip_address')
    op.drop_column('nodes', 'description')
    op.drop_column('nodes', 'status')
    op.drop_column('pools', 'current_instances')
    op.drop_column('pools', 'status')
    
    # Drop created tables
    op.drop_table('audit_logs')
    op.drop_table('system_analytics')
    op.drop_table('pool_analytics')
    op.drop_table('node_heartbeats')
    op.drop_table('node_configurations')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS nodestatus')
    op.execute('DROP TYPE IF EXISTS poolstatus')
