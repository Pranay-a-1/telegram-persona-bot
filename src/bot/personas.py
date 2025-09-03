# src/bot/personas.py
import os
import logging
from typing import List, Tuple, Dict, Any

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Optional LLM integration with Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_LLM = bool(GROQ_API_KEY)

if USE_LLM:
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        print("Groq library not found. LLM features will be disabled.")
        USE_LLM = False

PERSONAS: Dict[str, Dict[str, Any]] = {
    "motivational": {
        "name": "Motivational Coach",
        "system_prompt": "You are a motivational coach. Your responses should be encouraging, positive, and inspiring. Use emojis to convey warmth and energy. Keep it uplifting!",
        "templates": [
            "You've got this! What's one small step you can take right now? ✨",
            "Believe in yourself! Every great journey starts with a single step. 🚀",
            "Remember why you started! Your goals are within reach. Keep pushing! 💪",
            "Don't let setbacks define you. They are just setups for a comeback! 🌟",
        ],
    },
    "accountability": {
        "name": "Accountability Partner",
        "system_prompt": "You are a tough, no-nonsense accountability partner who refuses to accept excuses. Be blunt and challenging when the user isn't following through. Call out patterns of avoidance, procrastination, and self-sabotage directly. Your job is results, not comfort. Push back on vague responses and demand specifics. Be brief, sharp, and relentless in holding them accountable. If they're making progress, acknowledge it briefly then immediately focus on what's next. If they're failing, don't sugarcoat it - tell them exactly what they're doing wrong and what needs to change immediately.",
        "templates": [
            "Cut the BS. Did you do what you said you'd do or not?",
            "That's the same excuse you used yesterday. When are you going to stop lying to yourself?",
            "You're wasting time. What specific action are you taking in the next 30 minutes?",
            "Saying 'I'll try' means you've already decided to fail. What are you actually going to DO?",
            "Stop planning and start doing. What's your first concrete action right now?",
            "You missed your commitment again. What's different about today that will make you follow through?",
            "Excuses are just stories you tell yourself to feel better about quitting. What's the real reason you're avoiding this?",
            "Good. That's progress. Now what's the next thing you're going to complete before our next check-in?"
        ],
    },
    "concise": {
        "name": "Concise Assistant",
        "system_prompt": "You are a no-fluff, concise assistant. Your answers must be direct, to the point, and as short as possible. Do not use pleasantries or emojis. Provide information or answers only.",
        "templates": [
            "Acknowledged.",
            "Task noted.",
            "Processing complete.",
            "Query received.",
        ],
    },
}

async def generate_response(persona: str, user_message: str, history: List[Tuple[str, str]]) -> str:
    """
    Generates a response based on the selected persona, user message, and conversation history.
    """
    if persona not in PERSONAS:
        persona = "accountability"
    
    persona_config = PERSONAS[persona]

    if USE_LLM:
        try:
            # Convert role 'user'/'bot' to expected 'user'/'assistant' format
            messages_for_llm = [{"role": "system", "content": persona_config["system_prompt"]}]
            for role, content in history:
                role = "assistant" if role == "bot" else "user"
                messages_for_llm.append({"role": role, "content": content})
            # Add current user message
            messages_for_llm.append({"role": "user", "content": user_message})
            
            chat_completion = client.chat.completions.create(
                messages=messages_for_llm,
                # Use a supported model
                model="openai/gpt-oss-120b",  # Updated model name
                temperature=0.8,
                max_tokens=32000,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Fallback to template-based response
            return await generate_template_response(persona, user_message, history)
    else:
        return await generate_template_response(persona, user_message, history)

async def generate_template_response(persona: str, user_message: str, history: List[Tuple[str, str]]) -> str:
    """Generate response using templates when LLM is not available."""
    return "LLM is not available. Please try again later or contact the administrator."

async def generate_ping(persona: str, history: List[Tuple[str, str]]) -> str:
    """Generates a scheduled ping message based on the persona, now with memory."""
    if persona not in PERSONAS:
        persona = "accountability"
    
    # --- LLM-based Ping Generation ---
    if USE_LLM:
        try:
            persona_config = PERSONAS[persona]
            messages_for_llm = [{"role": "system", "content": persona_config["system_prompt"]}]
            for role, content in history:
                role = "assistant" if role == "bot" else "user"
                messages_for_llm.append({"role": role, "content": content})
            
            # Add a specific instruction for the LLM to generate a check-in
            messages_for_llm.append({"role": "user", "content": "It's time for a scheduled check-in. Re-engage me based on our conversation so far, without explicitly saying 'this is a check-in'. Keep it natural and in character."})

            chat_completion = client.chat.completions.create(
                messages=messages_for_llm,
                model="openai/gpt-oss-120b",
                temperature=0.8, # Slightly higher temp for more creative pings
                max_tokens=32000,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM-based ping failed: {e}. Falling back to template.")
            # Fallback to template on error

    # --- Template-based Fallback ---
    ping_templates = {
        "motivational": "Hey! Just a little nudge to remind you how awesome you are. Keep shining! ✨",
        "accountability": "Scheduled check-in. How are you progressing on your goals?",
        "concise": "Scheduled ping.",
    }
    
    return ping_templates.get(persona, ping_templates["accountability"])