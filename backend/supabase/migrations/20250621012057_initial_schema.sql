-- Create businesses table
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_user_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    business_id UUID REFERENCES businesses(id)
);

-- Create indexes for better performance
CREATE INDEX idx_users_clerk_user_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_business_id ON users(business_id);

-- Add comments for documentation
COMMENT ON TABLE businesses IS 'Companies or organizations in the system';
COMMENT ON TABLE users IS 'User accounts linked to Clerk authentication';
COMMENT ON COLUMN users.clerk_user_id IS 'Unique identifier from Clerk auth service';
COMMENT ON COLUMN users.business_id IS 'Optional link to a business/organization';
