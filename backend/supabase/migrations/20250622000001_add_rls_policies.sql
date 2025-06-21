-- Migration: Add Row Level Security policies for all user-related tables
-- This ensures data isolation between users

-- Enable RLS on oauth_tokens table
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;

-- Create policies for oauth_tokens
DROP POLICY IF EXISTS "Users can view their own oauth tokens" ON oauth_tokens;
CREATE POLICY "Users can view their own oauth tokens" ON oauth_tokens
  FOR SELECT USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert their own oauth tokens" ON oauth_tokens;
CREATE POLICY "Users can insert their own oauth tokens" ON oauth_tokens
  FOR INSERT WITH CHECK (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update their own oauth tokens" ON oauth_tokens;
CREATE POLICY "Users can update their own oauth tokens" ON oauth_tokens
  FOR UPDATE USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can delete their own oauth tokens" ON oauth_tokens;
CREATE POLICY "Users can delete their own oauth tokens" ON oauth_tokens
  FOR DELETE USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

-- Enable RLS on emails table
ALTER TABLE emails ENABLE ROW LEVEL SECURITY;

-- Create policies for emails
DROP POLICY IF EXISTS "Users can view their own emails" ON emails;
CREATE POLICY "Users can view their own emails" ON emails
  FOR SELECT USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert their own emails" ON emails;
CREATE POLICY "Users can insert their own emails" ON emails
  FOR INSERT WITH CHECK (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update their own emails" ON emails;
CREATE POLICY "Users can update their own emails" ON emails
  FOR UPDATE USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can delete their own emails" ON emails;
CREATE POLICY "Users can delete their own emails" ON emails
  FOR DELETE USING (
    user_id IN (
      SELECT id FROM users WHERE supabase_user_id = auth.uid()
    )
  );

-- Enable RLS on email_attachments table
ALTER TABLE email_attachments ENABLE ROW LEVEL SECURITY;

-- Create policies for email_attachments
DROP POLICY IF EXISTS "Users can view their own email attachments" ON email_attachments;
CREATE POLICY "Users can view their own email attachments" ON email_attachments
  FOR SELECT USING (
    email_id IN (
      SELECT e.id FROM emails e
      JOIN users u ON e.user_id = u.id
      WHERE u.supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can insert their own email attachments" ON email_attachments;
CREATE POLICY "Users can insert their own email attachments" ON email_attachments
  FOR INSERT WITH CHECK (
    email_id IN (
      SELECT e.id FROM emails e
      JOIN users u ON e.user_id = u.id
      WHERE u.supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can update their own email attachments" ON email_attachments;
CREATE POLICY "Users can update their own email attachments" ON email_attachments
  FOR UPDATE USING (
    email_id IN (
      SELECT e.id FROM emails e
      JOIN users u ON e.user_id = u.id
      WHERE u.supabase_user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Users can delete their own email attachments" ON email_attachments;
CREATE POLICY "Users can delete their own email attachments" ON email_attachments
  FOR DELETE USING (
    email_id IN (
      SELECT e.id FROM emails e
      JOIN users u ON e.user_id = u.id
      WHERE u.supabase_user_id = auth.uid()
    )
  ); 