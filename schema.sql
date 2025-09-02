-- schema.sql

-- Stores user-specific settings. Since it's a single-user bot, it will only have one row.
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER PRIMARY KEY,
    persona TEXT NOT NULL DEFAULT 'accountability',
    timezone TEXT NOT NULL DEFAULT 'UTC'
);

-- Stores the history of messages for context.
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL, -- 'user' or 'bot'
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster message retrieval
CREATE INDEX IF NOT EXISTS idx_messages_user_id_timestamp ON messages (user_id, timestamp);

-- Stores the scheduled ping times for the user.
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ping_time TEXT NOT NULL, -- Stored as HH:MM string
    UNIQUE(user_id, ping_time)
);
