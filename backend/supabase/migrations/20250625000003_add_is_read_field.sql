-- Add is_read field to emails table
ALTER TABLE emails 
ADD COLUMN is_read BOOLEAN DEFAULT FALSE;

-- Create index for better performance when filtering unread emails
CREATE INDEX idx_emails_is_read ON emails(is_read);

-- Add comment for documentation
COMMENT ON COLUMN emails.is_read IS 'Whether the email has been read by the user'; 