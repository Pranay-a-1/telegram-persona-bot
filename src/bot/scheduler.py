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
DATABASE_URL = f"sqlite:///{os.getenv('DATABASE_PATH', 'bot_data.db')}"
OWNER_ID_STR = os.getenv("OWNER_TELEGRAM_ID")
OWNER_ID = int(OWNER_ID_STR) if OWNER_ID_STR else 0
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Get the token for pickling

# --- Scheduler Setup ---
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=os.getenv("TIMEZONE", "UTC"))

async def send_ping(bot_token: str, user_id: int):
    """
    The job function that sends a scheduled message.
    It creates a temporary Bot instance to avoid pickling issues.
    """
    try:
        # Create a lightweight, temporary bot instance just for this task
        bot = Bot(token=bot_token)
        current_persona = await db_utils.get_user_setting(user_id, 'persona')
        message = await generate_ping(current_persona)
        await bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Sent scheduled ping to user {user_id} at {datetime.now()}")
    except Exception as e:
        logger.error(f"Failed to send ping to {user_id}: {e}", exc_info=True)

async def sync_and_reschedule_jobs():
    """
    Clears existing jobs and schedules new ones based on the database config.
    This function no longer needs the bot object passed to it.
    """
    if not OWNER_ID or not TELEGRAM_TOKEN:
        logger.warning("OWNER_TELEGRAM_ID or TELEGRAM_BOT_TOKEN not set. Scheduler cannot run.")
        return

    logger.info("Syncing and rescheduling jobs...")
    
    # Remove all existing jobs for the owner to avoid duplicates
    removed = 0
    for job in scheduler.get_jobs():
        # Check args safely before accessing index
        if job.args and len(job.args) > 1 and job.args[1] == OWNER_ID:
            job.remove()
            removed += 1
            logger.info(f"Removed existing job: {job.id}")
    if removed == 0:
        logger.info("No existing jobs to remove.")

    # Fetch schedule and timezone from DB
    schedule_times = await db_utils.get_schedule(OWNER_ID)
    user_timezone_str = await db_utils.get_user_setting(OWNER_ID, 'timezone')
    logger.info(f"Fetched schedule times: {schedule_times} with timezone: {user_timezone_str}")
    
    # Schedule new jobs
    for time_str in schedule_times:
        hour, minute = map(int, time_str.split(':'))
        job_id = f"ping_{OWNER_ID}_{hour}_{minute}"
        logger.info(f"Scheduling job {job_id} for {time_str} in timezone {user_timezone_str}")
        scheduler.add_job(
            send_ping,
            'cron',
            hour=hour,
            minute=minute,
            timezone=pytz.timezone(user_timezone_str),
            id=job_id,
            # Pass the TOKEN (a string) instead of the bot object
            args=[TELEGRAM_TOKEN, OWNER_ID],
            replace_existing=True,
            misfire_grace_time=3600
        )
    if scheduler.get_jobs():
        logger.info("Current scheduled jobs:")
        for job in scheduler.get_jobs():
            logger.info(f"- Job ID: {job.id}, Trigger: {job.trigger}, Next run: {job.next_run_time}")
    else:
        logger.warning("No jobs scheduled after sync!")
