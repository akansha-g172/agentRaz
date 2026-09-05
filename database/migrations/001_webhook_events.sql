CREATE TABLE IF NOT EXISTS processed_webhook_events (
    event_id VARCHAR(100) PRIMARY KEY,
    event_type VARCHAR(100),
    payload JSONB DEFAULT '{}'::jsonb,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
