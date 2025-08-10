-- Migration: Add Slack provider to connection_provider enum
-- This allows users to connect Slack workspaces alongside Gmail

-- Add slack to the connection_provider enum
ALTER TYPE connection_provider ADD VALUE 'slack';

-- Add comments for documentation
COMMENT ON TYPE connection_provider IS 'Available connection providers: gmail, slack'; 