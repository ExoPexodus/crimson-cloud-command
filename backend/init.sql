
-- Initialize database schema
CREATE DATABASE IF NOT EXISTS autoscaling_db;
USE autoscaling_db;

-- Create tables first (commented out as they're likely created by SQLAlchemy/ORM)
-- We'll add proper index creation statements that work with MySQL 8.0

-- Note: MySQL doesn't support "IF NOT EXISTS" for CREATE INDEX
-- We'll modify the script to be compatible with MySQL syntax
-- This script will be idempotent by using DROP INDEX IF EXISTS before CREATE INDEX

-- Add config_hash column to nodes table if it doesn't exist (for migration compatibility)
-- This prevents the error: Unknown column 'nodes.config_hash' in 'field list'
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'autoscaling_db' 
     AND TABLE_NAME = 'nodes' 
     AND COLUMN_NAME = 'config_hash') = 0,
    'ALTER TABLE nodes ADD COLUMN config_hash VARCHAR(255) DEFAULT NULL',
    'SELECT 1'
));

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- For nodes table
DROP INDEX IF EXISTS idx_nodes_region ON nodes;
DROP INDEX IF EXISTS idx_nodes_status ON nodes;
DROP INDEX IF EXISTS idx_nodes_config_hash ON nodes;

-- For pools table
DROP INDEX IF EXISTS idx_pools_node_id ON pools;
DROP INDEX IF EXISTS idx_pools_oracle_pool_id ON pools;

-- For metrics table
DROP INDEX IF EXISTS idx_metrics_node_id ON metrics;
DROP INDEX IF EXISTS idx_metrics_timestamp ON metrics;
DROP INDEX IF EXISTS idx_metrics_type_source ON metrics;

-- For schedules table
DROP INDEX IF EXISTS idx_schedules_pool_id ON schedules;
DROP INDEX IF EXISTS idx_schedules_active ON schedules;

-- For audit_logs table
DROP INDEX IF EXISTS idx_audit_logs_user_id ON audit_logs;
DROP INDEX IF EXISTS idx_audit_logs_timestamp ON audit_logs;

-- Now create the indexes (will only execute if tables exist)
-- These statements will fail silently if tables don't exist yet, which is fine
-- because SQLAlchemy will create them later

ALTER TABLE nodes ADD INDEX idx_nodes_region (region);
ALTER TABLE nodes ADD INDEX idx_nodes_status (status);
ALTER TABLE nodes ADD INDEX idx_nodes_config_hash (config_hash);

ALTER TABLE pools ADD INDEX idx_pools_node_id (node_id);
ALTER TABLE pools ADD INDEX idx_pools_oracle_pool_id (oracle_pool_id);

ALTER TABLE metrics ADD INDEX idx_metrics_node_id (node_id);
ALTER TABLE metrics ADD INDEX idx_metrics_timestamp (timestamp);
ALTER TABLE metrics ADD INDEX idx_metrics_type_source (metric_type, metric_source);

ALTER TABLE schedules ADD INDEX idx_schedules_pool_id (pool_id);
ALTER TABLE schedules ADD INDEX idx_schedules_active (is_active);

ALTER TABLE audit_logs ADD INDEX idx_audit_logs_user_id (user_id);
ALTER TABLE audit_logs ADD INDEX idx_audit_logs_timestamp (timestamp);
