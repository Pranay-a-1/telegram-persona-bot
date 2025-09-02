# src/bot/memory.py
import csv
import io
from typing import List, Tuple
from database import db_utils

async def get_formatted_memory(user_id: int) -> str:
    """
    Retrieves the last 50 messages and formats them into a string.
    """
    messages = await db_utils.get_last_n_messages(user_id, 50)
    if not messages:
        return "No recent conversation history."
    
    # Format for simple text display or for LLM context
    history = "\n".join([f"{role.capitalize()}: {content}" for role, content in messages])
    return f"--- Recent Conversation ---\n{history}"

async def export_memory_as_csv(user_id: int):
    """
    Exports the user's message history as a CSV file content.
    """
    messages = await db_utils.get_last_n_messages(user_id, 50)
    if not messages:
        return None

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['role', 'content'])
    writer.writerows(messages)
    
    output.seek(0)
    return output.read().encode('utf-8')
