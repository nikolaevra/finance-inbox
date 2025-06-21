-- Migration: Update users table for Supabase Auth
-- This migration updates the users table to work with Supabase Auth instead of Clerk

-- Step 1: Drop the old Clerk-specific column and index
DROP INDEX IF EXISTS idx_users_clerk_user_id;

-- Step 2: Add new columns (nullable first to handle existing data)
ALTER TABLE users ADD COLUMN IF NOT EXISTS supabase_user_id UUID;
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_sign_in_at TIMESTAMP WITH TIME ZONE;

-- Step 3: Clear existing users table (since we can't map Clerk IDs to Supabase Auth)
-- This is necessary because existing Clerk users don't exist in Supabase Auth
DELETE FROM email_attachments WHERE email_id IN (SELECT id FROM emails);
DELETE FROM emails;
DELETE FROM oauth_tokens;
DELETE FROM users;

-- Step 4: Drop the old clerk_user_id column
ALTER TABLE users DROP COLUMN IF EXISTS clerk_user_id;

-- Step 5: Now add constraints to the empty table
ALTER TABLE users ALTER COLUMN supabase_user_id SET NOT NULL;
ALTER TABLE users ADD CONSTRAINT users_supabase_user_id_unique UNIQUE (supabase_user_id);
ALTER TABLE users ADD CONSTRAINT users_supabase_user_id_fkey FOREIGN KEY (supabase_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

-- Step 6: Create indexes for better performance
CREATE INDEX idx_users_supabase_user_id ON users(supabase_user_id);

-- Step 7: Update comments for documentation
COMMENT ON TABLE users IS 'User profiles linked to Supabase authentication';
COMMENT ON COLUMN users.supabase_user_id IS 'References auth.users.id from Supabase Auth';
COMMENT ON COLUMN users.email IS 'User email address (synced with auth.users.email)';
COMMENT ON COLUMN users.full_name IS 'User display name';
COMMENT ON COLUMN users.avatar_url IS 'URL to user profile picture';
COMMENT ON COLUMN users.last_sign_in_at IS 'Last successful authentication timestamp';

-- Step 8: Create a function to automatically create user profiles when auth users are created
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (supabase_user_id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 9: Create trigger to automatically create user profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Step 10: Enable Row Level Security (RLS) for users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Step 11: Create RLS policies
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
CREATE POLICY "Users can view their own profile" ON users
  FOR SELECT USING (supabase_user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update their own profile" ON users;
CREATE POLICY "Users can update their own profile" ON users
  FOR UPDATE USING (supabase_user_id = auth.uid());

DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON users;
CREATE POLICY "Enable insert for authenticated users only" ON users
  FOR INSERT WITH CHECK (supabase_user_id = auth.uid()); 