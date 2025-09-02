# src/database/db_utils.py
import aiosqlite
import logging
import os
from typing import List, Tuple

DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.db")
OWNER_ID = int(os.getenv("OWNER_TELEGRAM_ID", 0))
DEFAULT_TIMEZONE = os.getenv("TIMEZONE", "UTC")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def initialize_database():
    """Initializes the database and creates tables if they don't exist."""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            with open('schema.sql', 'r') as f:
                await db.executescript(f.read())

            # Check if default settings and schedule exist for the owner
            cursor = await db.execute("SELECT * FROM settings WHERE user_id = ?", (OWNER_ID,))
            if await cursor.fetchone() is None:
                await db.execute(
                    "INSERT INTO settings (user_id, timezone) VALUES (?, ?)",
                    (OWNER_ID, DEFAULT_TIMEZONE)
                )
                logger.info(f"Initialized settings for owner {OWNER_ID}")

            cursor = await db.execute("SELECT * FROM schedule WHERE user_id = ?", (OWNER_ID,))
            if await cursor.fetchone() is None:
                default_times = ["14:13","14:15", "17:00", "23:00"]
                for time_str in default_times:
                    await db.execute(
                        "INSERT INTO schedule (user_id, ping_time) VALUES (?, ?)",
                        (OWNER_ID, time_str)
                    )
                logger.info(f"Initialized default schedule for owner {OWNER_ID}")

            await db.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)

async def get_db_connection():
    """Returns an async database connection."""
    return await aiosqlite.connect(DATABASE_PATH)

async def get_user_setting(user_id: int, setting_name: str) -> str:
    """Retrieves a specific setting for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(f"SELECT {setting_name} FROM settings WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else (DEFAULT_TIMEZONE if setting_name == 'timezone' else 'accountability')

async def update_user_setting(user_id: int, setting_name: str, value: str):
    """Updates a specific setting for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE settings SET {setting_name} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()

async def get_schedule(user_id: int) -> List[str]:
    """Retrieves the schedule for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT ping_time FROM schedule WHERE user_id = ? ORDER BY ping_time", (user_id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def update_schedule(user_id: int, times: List[str]):
    """Updates the entire schedule for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM schedule WHERE user_id = ?", (user_id,))
        for time_str in times:
            await db.execute("INSERT INTO schedule (user_id, ping_time) VALUES (?, ?)", (user_id, time_str))
        await db.commit()

async def add_message(user_id: int, role: str, content: str):
    """Adds a message to the history and enforces the 50-message limit."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        # Enforce the 50 message limit by deleting the oldest message
        await db.execute("""
            DELETE FROM messages WHERE id IN (
                SELECT id FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT -1 OFFSET 50
            )
        """, (user_id,))
        await db.commit()

async def get_last_n_messages(user_id: int, n: int = 50) -> List[Tuple[str, str]]:
    """Retrieves the last N messages for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, n)
        )
        rows = await cursor.fetchall()
        return list(reversed(rows)) # Return in chronological order

async def clear_memory(user_id: int):
    """Deletes all messages for a user."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        await db.commit()
