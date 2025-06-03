
-- Migration to add config_hash column to nodes table
-- This fixes the OperationalError: Unknown column 'nodes.config_hash'

USE autoscaling_db;

-- Add config_hash column to nodes table if it doesn't exist
ALTER TABLE nodes 
ADD COLUMN IF NOT EXISTS config_hash VARCHAR(255) DEFAULT NULL;

-- Create an index on config_hash for better performance
CREATE INDEX IF NOT EXISTS idx_nodes_config_hash ON nodes(config_hash);

-- Update any existing nodes to have a default config_hash
UPDATE nodes SET config_hash = 'default_config_hash' WHERE config_hash IS NULL;

