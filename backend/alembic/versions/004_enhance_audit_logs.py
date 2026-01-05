"""Enhance audit logs table for enterprise-level auditing

Revision ID: 004_enhance_audit_logs
Revises: 003_add_node_lifecycle_log
Create Date: 2025-01-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_enhance_audit_logs'
down_revision = '003_add_node_lifecycle_log'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old audit_logs table if it exists and recreate with new schema
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE")
    
    # Create enhanced audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('user_role', sa.String(50), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),  # AUTH, NODE, POOL, USER, CONFIG, SYSTEM
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('resource_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),  # JSON data for additional context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='SUCCESS'),  # SUCCESS, FAILURE
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_category', 'audit_logs', ['category'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])


def downgrade():
    op.drop_index('ix_audit_logs_resource_type', 'audit_logs')
    op.drop_index('ix_audit_logs_timestamp', 'audit_logs')
    op.drop_index('ix_audit_logs_category', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    op.drop_index('ix_audit_logs_user_id', 'audit_logs')
    op.drop_table('audit_logs')
    
    # Recreate original audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
