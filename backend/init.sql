
-- Initialize database schema
CREATE DATABASE IF NOT EXISTS autoscaling_db;
USE autoscaling_db;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_nodes_region ON nodes(region);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_pools_node_id ON pools(node_id);
CREATE INDEX IF NOT EXISTS idx_pools_oracle_pool_id ON pools(oracle_pool_id);
CREATE INDEX IF NOT EXISTS idx_metrics_node_id ON metrics(node_id);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_type_source ON metrics(metric_type, metric_source);
CREATE INDEX IF NOT EXISTS idx_schedules_pool_id ON schedules(pool_id);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
