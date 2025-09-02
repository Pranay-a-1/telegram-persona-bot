# src/bot/handlers.py
import logging
import os
import re
from functools import wraps

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from database import db_utils
from bot import memory, personas, scheduler

# --- Constants ---
OWNER_ID = int(os.getenv("OWNER_TELEGRAM_ID", 0))
VALID_PERSONAS = list(personas.PERSONAS.keys())

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Decorator for Owner-Only Commands ---
def owner_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != OWNER_ID:
            logger.warning(f"Unauthorized access denied for {user_id}.")
            await update.message.reply_text("This bot is for private use only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- Command Handlers ---
@owner_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user_id = update.effective_user.id
    current_persona = await db_utils.get_user_setting(user_id, 'persona')
    persona_name = personas.PERSONAS.get(current_persona, {}).get('name', 'Default')

    await update.message.reply_text(
        f"Hello! I am your personal assistant.\n"
        f"Current Persona: **{persona_name}**\n\n"
        "Available commands:\n"
        "/personas - List available personas\n"
        "/set_persona <name> - Switch my personality\n"
        "/set_times HH:MM HH:MM ... - Configure daily ping times\n"
        "/memory_clear - Clear our conversation history\n"
        "/export_memory - Export our conversation as a CSV file"
    )

@owner_only
async def set_persona_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /set_persona command."""
    user_id = update.effective_user.id
    try:
        new_persona = context.args[0].lower()
        if new_persona not in VALID_PERSONAS:
            await update.message.reply_text(f"Invalid persona. Please choose from: {', '.join(VALID_PERSONAS)}")
            return
        
        await db_utils.update_user_setting(user_id, 'persona', new_persona)
        persona_name = personas.PERSONAS[new_persona]['name']
        await update.message.reply_text(f"Persona switched to: **{persona_name}**")
        logger.info(f"User {user_id} switched persona to {new_persona}")

    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set_persona <name>\n"
                                        f"Example: /set_persona motivational")

@owner_only
async def list_personas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /personas command."""
    message = "Available Personas:\n"
    for key, data in personas.PERSONAS.items():
        message += f"- **{key}**: {data['name']}\n"
    await update.message.reply_text(message)

@owner_only
async def set_times_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /set_times command."""
    user_id = update.effective_user.id
    if not context.args:
        current_schedule = await db_utils.get_schedule(user_id)
        current_tz = await db_utils.get_user_setting(user_id, 'timezone')
        await update.message.reply_text(
            f"Current schedule ({current_tz}): {', '.join(current_schedule)}\n"
            "Usage: /set_times HH:MM HH:MM ...\n"
            "Example: /set_times 09:00 12:30 22:00"
        )
        return

    new_times = []
    time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
    for time_str in context.args:
        if time_pattern.match(time_str):
            new_times.append(time_str)
        else:
            await update.message.reply_text(f"Invalid time format: {time_str}. Please use HH:MM.")
            return
    
    await db_utils.update_schedule(user_id, new_times)
    await scheduler.sync_and_reschedule_jobs() # Reschedule jobs
    
    await update.message.reply_text(f"Ping schedule updated to: {', '.join(new_times)}")
    logger.info(f"User {user_id} updated schedule to {new_times}")

@owner_only
async def clear_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /memory_clear command."""
    user_id = update.effective_user.id
    await db_utils.clear_memory(user_id)
    await update.message.reply_text("Conversation memory has been cleared.")
    logger.info(f"Memory cleared for user {user_id}")

@owner_only
async def export_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /export_memory command."""
    user_id = update.effective_user.id
    csv_data = await memory.export_memory_as_csv(user_id)
    if csv_data:
        await update.message.reply_document(
            document=InputFile(csv_data, filename="conversation_history.csv"),
            caption="Here is your conversation history."
        )
    else:
        await update.message.reply_text("No conversation history to export.")

# --- Message Handler ---
@owner_only
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all non-command text messages."""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Store user message
    await db_utils.add_message(user_id, 'user', user_message)
    
    # Get context for response generation
    current_persona = await db_utils.get_user_setting(user_id, 'persona')
    history = await db_utils.get_last_n_messages(user_id, n=20) # Use last 20 messages for context

    # Generate and send response
    bot_response = await personas.generate_response(current_persona, user_message, history)
    await update.message.reply_text(bot_response)
    
    # Store bot response
    await db_utils.add_message(user_id, 'bot', bot_response)

# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Logs errors caused by updates."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
