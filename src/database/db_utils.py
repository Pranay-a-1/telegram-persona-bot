# src/database/db_utils.py
import asyncpg
import logging
import os
from typing import List, Tuple

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
    """Initializes the database and creates tables if they don't exist."""
    try:
        async with POOL.acquire() as conn:
            with open('schema.sql', 'r') as f:
                await conn.execute(f.read())

            # Check if default settings and schedule exist for the owner
            row = await conn.fetchrow("SELECT * FROM settings WHERE user_id = $1", OWNER_ID)
            if row is None:
                await conn.execute(
                    "INSERT INTO settings (user_id, timezone) VALUES ($1, $2)",
                    OWNER_ID, DEFAULT_TIMEZONE
                )
                logger.info(f"Initialized settings for owner {OWNER_ID}")

            row = await conn.fetchrow("SELECT * FROM schedule WHERE user_id = $1", OWNER_ID)
            if row is None:
                default_times = ["14:13", "14:15", "17:00", "23:00"]
                for time_str in default_times:
                    await conn.execute(
                        "INSERT INTO schedule (user_id, ping_time) VALUES ($1, $2)",
                        OWNER_ID, time_str
                    )
                logger.info(f"Initialized default schedule for owner {OWNER_ID}")
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)


async def get_user_setting(user_id: int, setting_name: str) -> str:
    """Retrieves a specific setting for a user."""
    async with POOL.acquire() as conn:
        row = await conn.fetchrow(f"SELECT {setting_name} FROM settings WHERE user_id = $1", user_id)
        return row[setting_name] if row else (DEFAULT_TIMEZONE if setting_name == 'timezone' else 'accountability')

async def update_user_setting(user_id: int, setting_name: str, value: str):
    """Updates a specific setting for a user."""
    async with POOL.acquire() as conn:
        await conn.execute(f"UPDATE settings SET {setting_name} = $1 WHERE user_id = $2", value, user_id)

async def get_schedule(user_id: int) -> List[str]:
    """Retrieves the schedule for a user."""
    async with POOL.acquire() as conn:
        rows = await conn.fetch("SELECT ping_time FROM schedule WHERE user_id = $1 ORDER BY ping_time", user_id)
        return [row['ping_time'] for row in rows]

async def update_schedule(user_id: int, times: List[str]):
    """Updates the entire schedule for a user."""
    async with POOL.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM schedule WHERE user_id = $1", user_id)
            for time_str in times:
                await conn.execute("INSERT INTO schedule (user_id, ping_time) VALUES ($1, $2)", user_id, time_str)

async def add_message(user_id: int, role: str, content: str):
    """Adds a message to the history and enforces the 50-message limit."""
    async with POOL.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO messages (user_id, role, content) VALUES ($1, $2, $3)",
                user_id, role, content
            )
            # Enforce the 50 message limit by deleting the oldest message
            await conn.execute("""
                DELETE FROM messages WHERE id IN (
                    SELECT id FROM messages WHERE user_id = $1 ORDER BY timestamp DESC OFFSET 50
                )
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
