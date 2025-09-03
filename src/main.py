# src/main.py
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# --- Add src to Python path for proper imports ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Load Environment Variables ---
# This MUST be at the top, before any other local modules are imported.
load_dotenv()

from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import using relative imports since we're in src/
from database import db_utils
from bot import handlers, scheduler

# --- Setup Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Get Environment Variables ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_TELEGRAM_ID")
PORT = int(os.getenv("PORT", 8000))  # Railway provides PORT automatically

async def main():
    """Initializes and runs the bot application."""
    
    if not TELEGRAM_TOKEN or not OWNER_ID:
        logger.critical("TELEGRAM_BOT_TOKEN or OWNER_TELEGRAM_ID environment variable not set. Exiting.")
        return
    
    # Initialize the database connection pool first
    await db_utils.init_pool()
    await db_utils.initialize_database()

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("set_persona", handlers.set_persona_command))
    application.add_handler(CommandHandler("personas", handlers.list_personas_command))
    application.add_handler(CommandHandler("set_schedule", handlers.set_schedule_command))
    application.add_handler(CommandHandler("memory_clear", handlers.clear_memory_command))
    application.add_handler(CommandHandler("export_memory", handlers.export_memory_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    application.add_error_handler(handlers.error_handler)

    try:
        # Start the scheduler FIRST
        if not scheduler.scheduler.running:
            scheduler.scheduler.start()
            logger.info("Scheduler started.")
        else:
            logger.info("Scheduler was already running.")

        # THEN, sync the jobs
        await scheduler.sync_and_reschedule_jobs()

        # Initialize and start the bot application
        await application.initialize()
        await application.start()
        
        # For Railway deployment - use simple polling
        if os.getenv("RAILWAY_ENVIRONMENT"):
            await application.updater.start_polling()
            logger.info("Bot started with polling for Railway deployment.")
        else:
            # Local development
            await application.updater.start_polling()
            logger.info("Bot started with polling for local development.")

        # Keep the script running
        while True:
            await asyncio.sleep(3600)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutdown signal received.")
    finally:
        logger.info("Shutting down bot and scheduler...")
        if scheduler.scheduler.running:
            scheduler.scheduler.shutdown()
            logger.info("Scheduler shut down.")
        
        if application.running:
            await application.shutdown()
            logger.info("Bot application has been shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        logger.error(f"Failed to run the bot due to an asyncio error: {e}")
