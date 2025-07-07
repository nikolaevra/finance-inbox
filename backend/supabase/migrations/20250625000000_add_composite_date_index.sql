-- Add composite index for user_id and date_sent for optimized sorting
-- This will significantly improve performance when filtering by user and sorting by date

CREATE INDEX idx_emails_user_date_sent_desc ON emails(user_id, date_sent DESC);
CREATE INDEX idx_emails_user_date_sent_asc ON emails(user_id, date_sent ASC);

-- Add composite index for user_id and thread_id for thread queries
CREATE INDEX idx_emails_user_thread_date ON emails(user_id, thread_id, date_sent DESC);

-- Add comments for documentation
COMMENT ON INDEX idx_emails_user_date_sent_desc IS 'Composite index for user filtering with descending date sorting (inbox view)';
COMMENT ON INDEX idx_emails_user_date_sent_asc IS 'Composite index for user filtering with ascending date sorting (thread view)';
COMMENT ON INDEX idx_emails_user_thread_date IS 'Composite index for user and thread filtering with date sorting'; 