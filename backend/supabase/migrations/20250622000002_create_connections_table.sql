-- Migration: Create connections table
-- This table tracks user connections to external services (Gmail, etc.)

-- Create enum types for connection status and provider
CREATE TYPE connection_status AS ENUM ('connected', 'disconnected', 'refresh_required');
CREATE TYPE connection_provider AS ENUM ('gmail');

-- Create connections table
CREATE TABLE connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    connection_provider connection_provider NOT NULL,
    status connection_status NOT NULL DEFAULT 'disconnected',
    oauth_token_id UUID REFERENCES oauth_tokens(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    
    -- Ensure one connection per user per provider
    UNIQUE(user_id, connection_provider)
);

-- Create indexes for better performance
CREATE INDEX idx_connections_user_id ON connections(user_id);
CREATE INDEX idx_connections_provider ON connections(connection_provider);
CREATE INDEX idx_connections_status ON connections(status);
CREATE INDEX idx_connections_oauth_token_id ON connections(oauth_token_id);

-- Enable Row Level Security
ALTER TABLE connections ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for connections
CREATE POLICY "Users can view their own connections" ON connections
  FOR SELECT USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert their own connections" ON connections
  FOR INSERT WITH CHECK (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update their own connections" ON connections
  FOR UPDATE USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete their own connections" ON connections
  FOR DELETE USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_connections_updated_at
    BEFORE UPDATE ON connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE connections IS 'User connections to external services (Gmail, etc.)';
COMMENT ON COLUMN connections.user_id IS 'References users.id';
COMMENT ON COLUMN connections.connection_provider IS 'Type of service connected (gmail, etc.)';
COMMENT ON COLUMN connections.status IS 'Connection status (connected, disconnected, refresh_required)';
COMMENT ON COLUMN connections.oauth_token_id IS 'References oauth_tokens.id if applicable';
COMMENT ON COLUMN connections.last_sync_at IS 'Last time data was synced from this connection';
COMMENT ON COLUMN connections.metadata IS 'Provider-specific metadata (JSON)'; 