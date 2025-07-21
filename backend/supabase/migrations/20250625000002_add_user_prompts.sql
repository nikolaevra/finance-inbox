-- Create user_prompts table for storing customizable email categorization prompts
CREATE TABLE user_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Prompt configuration
    name VARCHAR(100) NOT NULL DEFAULT 'email_categorization',
    model VARCHAR(50) NOT NULL DEFAULT 'gpt-3.5-turbo',
    temperature DECIMAL(3,2) NOT NULL DEFAULT 0.1,
    max_tokens INTEGER NOT NULL DEFAULT 200,
    timeout INTEGER NOT NULL DEFAULT 10,
    prompt_version VARCHAR(50) NOT NULL DEFAULT '1.0',
    
    -- The actual prompt template
    template TEXT NOT NULL,
    
    -- Metadata
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_prompts_user_id ON user_prompts(user_id);
CREATE INDEX idx_user_prompts_active ON user_prompts(user_id, is_active);

-- Ensure only one active prompt per user per name
CREATE UNIQUE INDEX idx_user_prompts_unique_active ON user_prompts(user_id, name, is_active) 
WHERE is_active = TRUE;

-- Add comments
COMMENT ON TABLE user_prompts IS 'User-customizable prompts for email categorization';
COMMENT ON COLUMN user_prompts.user_id IS 'Reference to the user who owns this prompt';
COMMENT ON COLUMN user_prompts.name IS 'Prompt identifier (e.g., email_categorization)';
COMMENT ON COLUMN user_prompts.template IS 'The actual prompt template with {subject}, {sender}, {content} variables';
COMMENT ON COLUMN user_prompts.is_active IS 'Whether this prompt is currently active for the user';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_user_prompts_updated_at 
    BEFORE UPDATE ON user_prompts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column(); 