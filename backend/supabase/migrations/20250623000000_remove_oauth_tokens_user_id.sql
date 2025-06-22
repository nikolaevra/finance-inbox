-- Migration: Remove user_id from oauth_tokens table
-- The connections table will be the intermediary between users and oauth_tokens

-- Drop the existing RLS policies that depend on user_id
DROP POLICY IF EXISTS "Users can view their own oauth tokens" ON oauth_tokens;
DROP POLICY IF EXISTS "Users can insert their own oauth tokens" ON oauth_tokens;
DROP POLICY IF EXISTS "Users can update their own oauth tokens" ON oauth_tokens;
DROP POLICY IF EXISTS "Users can delete their own oauth tokens" ON oauth_tokens;

-- Remove the user_id column from oauth_tokens
ALTER TABLE oauth_tokens DROP COLUMN IF EXISTS user_id;

-- Create new RLS policies based on connections table
CREATE POLICY "Users can view oauth tokens through connections" ON oauth_tokens
  FOR SELECT USING (
    id IN (
      SELECT oauth_token_id FROM connections 
      WHERE user_id IN (
        SELECT id FROM users WHERE supabase_user_id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can insert oauth tokens through connections" ON oauth_tokens
  FOR INSERT WITH CHECK (true); -- Will be controlled by connections table

CREATE POLICY "Users can update oauth tokens through connections" ON oauth_tokens
  FOR UPDATE USING (
    id IN (
      SELECT oauth_token_id FROM connections 
      WHERE user_id IN (
        SELECT id FROM users WHERE supabase_user_id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can delete oauth tokens through connections" ON oauth_tokens
  FOR DELETE USING (
    id IN (
      SELECT oauth_token_id FROM connections 
      WHERE user_id IN (
        SELECT id FROM users WHERE supabase_user_id = auth.uid()
      )
    )
  );

-- Update comment
COMMENT ON TABLE oauth_tokens IS 'OAuth tokens for external services, linked through connections table'; 