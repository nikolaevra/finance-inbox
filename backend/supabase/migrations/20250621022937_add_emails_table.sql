-- Create emails table for storing Gmail emails
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    
    -- Gmail-specific identifiers
    gmail_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255),
    
    -- Email metadata
    subject TEXT,
    from_email TEXT,
    to_email TEXT,
    cc_email TEXT,
    bcc_email TEXT,
    reply_to TEXT,
    date_sent TIMESTAMP WITH TIME ZONE,
    
    -- Email content
    snippet TEXT,
    body_text TEXT,
    body_html TEXT,
    
    -- Gmail metadata
    labels TEXT[], -- Array of Gmail labels
    has_attachments BOOLEAN DEFAULT FALSE,
    size_estimate INTEGER,
    
    -- Processing metadata
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_emails_user_id ON emails(user_id);
CREATE INDEX idx_emails_gmail_id ON emails(gmail_id);
CREATE INDEX idx_emails_thread_id ON emails(thread_id);
CREATE INDEX idx_emails_date_sent ON emails(date_sent);
CREATE INDEX idx_emails_from_email ON emails(from_email);
CREATE INDEX idx_emails_subject ON emails USING gin(to_tsvector('english', subject));
CREATE INDEX idx_emails_labels ON emails USING gin(labels);
CREATE INDEX idx_emails_is_processed ON emails(is_processed);

-- Create unique constraint to prevent duplicate emails per user
CREATE UNIQUE INDEX idx_emails_user_gmail_unique ON emails(user_id, gmail_id);

-- Add comments for documentation
COMMENT ON TABLE emails IS 'Gmail emails stored for each user';
COMMENT ON COLUMN emails.user_id IS 'Reference to the user who owns this email';
COMMENT ON COLUMN emails.gmail_id IS 'Unique Gmail message ID';
COMMENT ON COLUMN emails.thread_id IS 'Gmail conversation thread ID';
COMMENT ON COLUMN emails.subject IS 'Email subject line';
COMMENT ON COLUMN emails.from_email IS 'Sender email address and name';
COMMENT ON COLUMN emails.to_email IS 'Primary recipient email address';
COMMENT ON COLUMN emails.date_sent IS 'When the email was originally sent';
COMMENT ON COLUMN emails.snippet IS 'Gmail auto-generated preview text';
COMMENT ON COLUMN emails.body_text IS 'Plain text version of email body';
COMMENT ON COLUMN emails.body_html IS 'HTML version of email body';
COMMENT ON COLUMN emails.labels IS 'Array of Gmail labels (INBOX, SENT, etc.)';
COMMENT ON COLUMN emails.has_attachments IS 'Whether email contains attachments';
COMMENT ON COLUMN emails.is_processed IS 'Whether email has been processed for analysis';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_emails_updated_at 
    BEFORE UPDATE ON emails 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create attachments table for email attachments
CREATE TABLE email_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE NOT NULL,
    
    -- Attachment metadata
    filename VARCHAR(255),
    mime_type VARCHAR(100),
    size_bytes INTEGER,
    
    -- Gmail attachment data
    attachment_id VARCHAR(255) NOT NULL, -- Gmail's attachment ID
    
    -- File storage (for future use)
    file_path TEXT, -- Path to stored file (if downloaded)
    is_downloaded BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for attachments
CREATE INDEX idx_attachments_email_id ON email_attachments(email_id);
CREATE INDEX idx_attachments_filename ON email_attachments(filename);
CREATE INDEX idx_attachments_mime_type ON email_attachments(mime_type);

-- Add comments for attachments table
COMMENT ON TABLE email_attachments IS 'Email attachments metadata and storage info';
COMMENT ON COLUMN email_attachments.email_id IS 'Reference to the parent email';
COMMENT ON COLUMN email_attachments.attachment_id IS 'Gmail attachment identifier';
COMMENT ON COLUMN email_attachments.file_path IS 'Local storage path if downloaded';

-- Create trigger for attachments updated_at
CREATE TRIGGER update_email_attachments_updated_at 
    BEFORE UPDATE ON email_attachments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
