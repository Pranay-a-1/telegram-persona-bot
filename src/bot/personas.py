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
        "system_prompt": "You are a firm but fair accountability partner. Be direct, ask clarifying questions, and help the user stay on track with their commitments. Your tone is supportive but serious. Be a no-fluff, concise assistant. Your answers must be direct, to the point, and as short as possible. Be encouraging, positive, and inspiring. Use emojis to convey warmth and energy. Keep it uplifting!",
        "templates": [
            "Checking in. What is the status of your primary goal for today?",
            "Did you complete the task you set out to do? If not, what were the blockers?",
            "Let's break it down. What's the very next action you need to take?",
            "A goal without a plan is just a wish. What's the plan?",
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
                temperature=0.7,
                max_tokens=8000,
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

async def generate_ping(persona: str) -> str:
    """Generates a scheduled ping message based on the persona."""
    if persona not in PERSONAS:
        persona = "accountability"
    
    ping_templates = {
        "motivational": "Hey! Just a little nudge to remind you how awesome you are. Keep shining! ✨",
        "accountability": "Scheduled check-in. How are you progressing on your goals?",
        "concise": "Scheduled ping.",
    }
    
    return ping_templates.get(persona, ping_templates["accountability"])