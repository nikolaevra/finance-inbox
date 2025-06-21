-- Create oauth_tokens table for storing Google OAuth tokens
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL DEFAULT 'google',
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(20) DEFAULT 'Bearer',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_oauth_tokens_user_id ON oauth_tokens(user_id);
CREATE INDEX idx_oauth_tokens_provider ON oauth_tokens(provider);
CREATE INDEX idx_oauth_tokens_expires_at ON oauth_tokens(expires_at);

-- Create unique constraint to prevent duplicate tokens per user/provider
CREATE UNIQUE INDEX idx_oauth_tokens_user_provider ON oauth_tokens(user_id, provider);

-- Add comments for documentation
COMMENT ON TABLE oauth_tokens IS 'OAuth tokens for external service integrations';
COMMENT ON COLUMN oauth_tokens.user_id IS 'Reference to the user who owns these tokens';
COMMENT ON COLUMN oauth_tokens.provider IS 'OAuth provider (google, microsoft, etc.)';
COMMENT ON COLUMN oauth_tokens.access_token IS 'Short-lived access token';
COMMENT ON COLUMN oauth_tokens.refresh_token IS 'Long-lived refresh token';
COMMENT ON COLUMN oauth_tokens.expires_at IS 'When the access token expires';
COMMENT ON COLUMN oauth_tokens.scope IS 'Granted OAuth scopes';

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_oauth_tokens_updated_at 
    BEFORE UPDATE ON oauth_tokens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
