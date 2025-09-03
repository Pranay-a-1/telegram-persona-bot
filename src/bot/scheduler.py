# src/bot/scheduler.py
import logging
import os
from datetime import datetime
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from telegram import Bot

from database import db_utils
from bot.personas import generate_ping

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
db_url_raw = os.getenv("DATABASE_URL")
if not db_url_raw:
    logger.warning("DATABASE_URL environment variable not set. Scheduler will use memory job store.")
    DATABASE_URL = None
else:
    # Replace asyncpg with psycopg2 for SQLAlchemy compatibility
    DATABASE_URL = db_url_raw.replace("asyncpg", "psycopg2")

OWNER_ID_STR = os.getenv("OWNER_TELEGRAM_ID")
OWNER_ID = int(OWNER_ID_STR) if OWNER_ID_STR else 0
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Scheduler Setup ---
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL) if DATABASE_URL else None
}
# Filter out None values, so APScheduler falls back to MemoryJobStore if DATABASE_URL is not set
jobstores = {k: v for k, v in jobstores.items() if v is not None}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=os.getenv("TIMEZONE", "UTC"))

async def send_ping(bot_token: str, user_id: int):
    """The job function that sends a scheduled message."""
    try:
        bot = Bot(token=bot_token)
        current_persona = await db_utils.get_user_setting(user_id, 'persona')
        # Fetch conversation history to make the ping context-aware
        history = await db_utils.get_last_n_messages(user_id, n=200)
        message = await generate_ping(current_persona, history) # Pass history to the generator
        await bot.send_message(chat_id=user_id, text=message)
        # Also, save the bot's ping to memory so it knows it just sent it
        await db_utils.add_message(user_id, 'bot', message)
        logger.info(f"Sent scheduled ping to user {user_id} at {datetime.now()}")
    except Exception as e:
        logger.error(f"Failed to send ping to {user_id}: {e}", exc_info=True)

async def sync_and_reschedule_jobs():
    """
    Clears ALL existing jobs for the owner and schedules a new one based on the
    ping frequency from the database, respecting the DND period (00:00-06:00).
    """
    if not OWNER_ID or not TELEGRAM_TOKEN:
        logger.warning("OWNER_TELEGRAM_ID or TELEGRAM_BOT_TOKEN not set. Scheduler cannot run.")
        return

    logger.info("Syncing and rescheduling jobs...")

    # --- Clear all previous jobs for the owner ---
    # This is crucial to remove any lingering jobs from the old format.
    removed_count = 0
    for job in scheduler.get_jobs():
        # The user_id is passed as the second argument to send_ping
        if job.args and len(job.args) > 1 and job.args[1] == OWNER_ID:
            job.remove()
            removed_count += 1
            logger.info(f"Removed existing job: {job.id}")
    
    if removed_count > 0:
        logger.info(f"Total of {removed_count} old jobs removed for user {OWNER_ID}.")
    else:
        logger.info(f"No existing jobs found for user {OWNER_ID}.")


    # --- Schedule the new single job ---
    job_id = f"ping_{OWNER_ID}"
    
    # Fetch new schedule settings
    frequency_hours = await db_utils.get_user_setting(OWNER_ID, 'ping_frequency_hours')
    user_timezone_str = await db_utils.get_user_setting(OWNER_ID, 'timezone')
    
    if frequency_hours is None or user_timezone_str is None:
        logger.error(f"Could not retrieve schedule settings for user {OWNER_ID}. Aborting reschedule.")
        return

    # --- Generate Cron Expression ---
    hour_cron = None
    minute_cron = '0'

    # Use a safer check for floating point numbers
    if frequency_hours < 1: # Handles 1 minutes (0.03) and any other fractional hour
        minute_cron = "*/1"
        hour_cron = "*" # Every hour
        logger.info(
            f"Scheduling job for user {OWNER_ID} with 2-minute frequency for testing."
        )
    else:
        # The "Do Not Disturb" period is from 00:00 to 05:59. Pings can start at 06:00.
        # The active period is from 06:00 to 23:59.
        hour_cron = f"6-23/{int(frequency_hours)}"
        if frequency_hours == 24:
            # For a 24-hour frequency, just ping once a day at the start of the active window.
            hour_cron = "6"
        logger.info(
            f"Scheduling job for user {OWNER_ID} with frequency {int(frequency_hours)} hours. "
            f"Cron hour expression: '{hour_cron}' in timezone {user_timezone_str}"
        )


    scheduler.add_job(
        send_ping,
        'cron',
        hour=hour_cron,
        minute=minute_cron,
        timezone=pytz.timezone(user_timezone_str),
        id=job_id,
        args=[TELEGRAM_TOKEN, OWNER_ID],
        replace_existing=True,
        misfire_grace_time=3600  # If the bot was offline, run jobs that are up to 1 hour late
    )

    if scheduler.get_jobs():
        logger.info("Current scheduled jobs:")
        for job in scheduler.get_jobs():
            logger.info(f"- Job ID: {job.id}, Trigger: {job.trigger}, Next run: {job.next_run_time}")
    else:
        logger.warning("No jobs scheduled after sync!")
