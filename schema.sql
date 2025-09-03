-- PostgreSQL schema for telegram-persona-bot

CREATE TABLE IF NOT EXISTS settings (
user_id BIGINT PRIMARY KEY,
persona TEXT NOT NULL DEFAULT 'accountability',
timezone TEXT NOT NULL DEFAULT 'UTC',
ping_frequency_hours REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS messages (
id SERIAL PRIMARY KEY,
user_id BIGINT NOT NULL,
role TEXT NOT NULL, -- 'user' or 'bot'
content TEXT NOT NULL,
timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster message retrieval
CREATE INDEX IF NOT EXISTS idx_messages_user_id_timestamp ON messages (user_id, timestamp);

-- The 'schedule' table is now obsolete and will be removed by the application logic.