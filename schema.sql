-- PostgreSQL schema for telegram-persona-bot

CREATE TABLE IF NOT EXISTS settings (
    user_id BIGINT PRIMARY KEY,
    persona TEXT NOT NULL DEFAULT 'accountability',
    timezone TEXT NOT NULL DEFAULT 'UTC'
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

CREATE TABLE IF NOT EXISTS schedule (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    ping_time TEXT NOT NULL,
    CONSTRAINT unique_user_ping_time UNIQUE(user_id, ping_time)
);
