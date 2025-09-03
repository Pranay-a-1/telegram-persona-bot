# src/database/db_utils.py
import asyncpg
import logging
import os
from typing import List, Tuple, Union

DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_ID = int(os.getenv("OWNER_TELEGRAM_ID", 0))
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "UTC")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

POOL = None

async def init_pool():
    """Initializes the asyncpg connection pool."""
    global POOL
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")
    POOL = await asyncpg.create_pool(dsn=DATABASE_URL)
    logger.info("Database connection pool initialized.")

async def initialize_database():
    """Initializes and migrates the database schema."""
    try:
        async with POOL.acquire() as conn:
            # --- Schema Initialization ---
            with open('src/bot/schema.sql', 'r') as f:
                # This will create tables if they don't exist
                await conn.execute(f.read())
            logger.info("Initial schema check complete. Tables created if they did not exist.")

            # --- Schema Migrations ---
            # Migration 1: Add ping_frequency_hours if it doesn't exist
            try:
                await conn.execute("ALTER TABLE settings ADD COLUMN ping_frequency_hours INTEGER NOT NULL DEFAULT 1;")
                logger.info("Migration successful: Added 'ping_frequency_hours' column to settings.")
            except asyncpg.exceptions.DuplicateColumnError:
                # Column already exists, which is fine.
                pass
            except Exception as e:
                logger.error(f"Error during 'ping_frequency_hours' migration: {e}")

            # Migration 2: Drop the old 'schedule' table if it exists
            try:
                await conn.execute("DROP TABLE IF EXISTS schedule;")
                logger.info("Migration successful: Dropped obsolete 'schedule' table.")
            except Exception as e:
                logger.error(f"Error dropping 'schedule' table: {e}")


            # --- Default Data Initialization for Owner ---
            # Check if default settings exist for the owner
            row = await conn.fetchrow("SELECT * FROM settings WHERE user_id = $1", OWNER_ID)
            if row is None:
                await conn.execute(
                    "INSERT INTO settings (user_id, timezone, persona, ping_frequency_hours) VALUES ($1, $2, $3, $4)",
                    OWNER_ID, DEFAULT_TIMEZONE, 'accountability', 1
                )
                logger.info(f"Initialized default settings for owner {OWNER_ID}")

        logger.info("Database initialized and migrations checked successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)


async def get_user_setting(user_id: int, setting_name: str) -> Union[str, int, None]:
    """Retrieves a specific setting for a user."""
    async with POOL.acquire() as conn:
        row = await conn.fetchrow(f"SELECT {setting_name} FROM settings WHERE user_id = $1", user_id)
        if not row:
            # Return defaults for specific settings if user record doesn't exist
            if setting_name == 'timezone': return DEFAULT_TIMEZONE
            if setting_name == 'persona': return 'accountability'
            if setting_name == 'ping_frequency_hours': return 1
            return None
        return row[setting_name]


async def update_user_setting(user_id: int, setting_name: str, value: Union[str, int]):
    """Updates a specific setting for a user."""
    async with POOL.acquire() as conn:
        # Use an UPSERT to handle cases where the user's settings row might not exist yet
        await conn.execute(
            f"""
            INSERT INTO settings (user_id, {setting_name}) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET {setting_name} = $2;
            """,
            user_id, value
        )


async def add_message(user_id: int, role: str, content: str):
    """Adds a message to the history and enforces the 50-message limit."""
    async with POOL.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO messages (user_id, role, content) VALUES ($1, $2, $3)",
                user_id, role, content
            )
            # Enforce the 50 message limit by deleting the oldest message
            # This is slightly inefficient but good enough for a single-user bot.
            # A better approach for multi-user systems would involve partitions or a cleanup job.
            await conn.execute("""
                DELETE FROM messages WHERE id IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp DESC) as rn
                        FROM messages WHERE user_id = $1
                    ) t WHERE t.rn > 50
                );
            """, user_id)


async def get_last_n_messages(user_id: int, n: int = 50) -> List[Tuple[str, str]]:
    """Retrieves the last N messages for a user."""
    async with POOL.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content FROM messages WHERE user_id = $1 ORDER BY timestamp DESC LIMIT $2",
            user_id, n
        )
        # Convert list of records to list of tuples
        return [(row['role'], row['content']) for row in reversed(rows)] # Return in chronological order

async def clear_memory(user_id: int):
    """Deletes all messages for a user."""
    async with POOL.acquire() as conn:
        await conn.execute("DELETE FROM messages WHERE user_id = $1", user_id)
