-- Add email categorization fields
ALTER TABLE emails ADD COLUMN category VARCHAR(100);
ALTER TABLE emails ADD COLUMN category_confidence DECIMAL(3,2);
ALTER TABLE emails ADD COLUMN categorized_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE emails ADD COLUMN category_prompt_version VARCHAR(50);

-- Create index for category filtering
CREATE INDEX idx_emails_category ON emails(category);
CREATE INDEX idx_emails_category_confidence ON emails(category_confidence);

-- Add comments for documentation
COMMENT ON COLUMN emails.category IS 'LLM-generated email category for financial professionals';
COMMENT ON COLUMN emails.category_confidence IS 'Confidence score from LLM (0.00-1.00)';
COMMENT ON COLUMN emails.categorized_at IS 'When the email was categorized';
COMMENT ON COLUMN emails.category_prompt_version IS 'Version of the prompt used for categorization'; 