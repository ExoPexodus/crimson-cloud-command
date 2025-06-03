
-- Initialize database schema for PostgreSQL
-- Note: SQLAlchemy will create the tables, this script only adds indexes for performance

-- Function to create index if it doesn't exist
CREATE OR REPLACE FUNCTION create_index_if_not_exists(index_name text, table_name text, column_name text)
RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = index_name
    ) THEN
        EXECUTE format('CREATE INDEX %I ON %I (%I)', index_name, table_name, column_name);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to create composite index if it doesn't exist
CREATE OR REPLACE FUNCTION create_composite_index_if_not_exists(index_name text, table_name text, columns text)
RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = index_name
    ) THEN
        EXECUTE format('CREATE INDEX %I ON %I (%s)', index_name, table_name, columns);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Wait for tables to be created by SQLAlchemy, then add indexes
-- This will be executed after the tables are created
DO $$
BEGIN
    -- Add a small delay to ensure tables are created first
    PERFORM pg_sleep(1);
    
    -- Check if tables exist before creating indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'nodes') THEN
        PERFORM create_index_if_not_exists('idx_nodes_region', 'nodes', 'region');
        PERFORM create_index_if_not_exists('idx_nodes_status', 'nodes', 'status');
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pools') THEN
        PERFORM create_index_if_not_exists('idx_pools_node_id', 'pools', 'node_id');
        PERFORM create_index_if_not_exists('idx_pools_oracle_pool_id', 'pools', 'oracle_pool_id');
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'metrics') THEN
        PERFORM create_index_if_not_exists('idx_metrics_node_id', 'metrics', 'node_id');
        PERFORM create_index_if_not_exists('idx_metrics_timestamp', 'metrics', 'timestamp');
        PERFORM create_composite_index_if_not_exists('idx_metrics_type_source', 'metrics', 'metric_type, metric_source');
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'schedules') THEN
        PERFORM create_index_if_not_exists('idx_schedules_pool_id', 'schedules', 'pool_id');
        PERFORM create_index_if_not_exists('idx_schedules_active', 'schedules', 'is_active');
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        PERFORM create_index_if_not_exists('idx_audit_logs_user_id', 'audit_logs', 'user_id');
        PERFORM create_index_if_not_exists('idx_audit_logs_timestamp', 'audit_logs', 'timestamp');
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pool_analytics') THEN
        PERFORM create_index_if_not_exists('idx_pool_analytics_pool_id', 'pool_analytics', 'pool_id');
        PERFORM create_index_if_not_exists('idx_pool_analytics_node_id', 'pool_analytics', 'node_id');
        PERFORM create_index_if_not_exists('idx_pool_analytics_timestamp', 'pool_analytics', 'timestamp');
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'node_heartbeats') THEN
        PERFORM create_index_if_not_exists('idx_node_heartbeats_node_id', 'node_heartbeats', 'node_id');
        PERFORM create_index_if_not_exists('idx_node_heartbeats_timestamp', 'node_heartbeats', 'timestamp');
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'node_configurations') THEN
        PERFORM create_index_if_not_exists('idx_node_configurations_node_id', 'node_configurations', 'node_id');
        PERFORM create_index_if_not_exists('idx_node_configurations_active', 'node_configurations', 'is_active');
    END IF;
END $$;

-- Clean up helper functions
DROP FUNCTION IF EXISTS create_index_if_not_exists(text, text, text);
DROP FUNCTION IF EXISTS create_composite_index_if_not_exists(text, text, text);
