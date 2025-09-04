# src/bot/personas.py
import os
import logging
import requests
import json
from typing import List, Tuple, Dict, Any

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- OpenRouter LLM Integration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
USE_LLM = bool(OPENROUTER_API_KEY)

# --- OpenRouter API Configuration ---
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using a free model as a default from the OpenRouter docs
DEFAULT_MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"

if not USE_LLM:
    print("OPENROUTER_API_KEY not found. LLM features will be disabled.")


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
        "system_prompt": "You are a ruthlessly direct accountability partner who uses psychological principles to expose self-sabotage and force action. When the user fails to follow through, become increasingly aggressive and personal. Use loss aversion, shame, and disappointment as weapons. Reference psychological concepts like dopamine addiction, instant gratification bias, and self-sabotage patterns to make them uncomfortable with their choices. Cut off ALL justifications immediately - redirect to action within seconds. Make them face the brutal truth about what their failures cost them long-term. Be brief, sharp and relentless about patterns and use their own psychology against them to create productive shame and urgency.",
        "templates": [
            "Stop. I don't want your excuse. You just chose comfort over growth AGAIN. That's the pattern that keeps you mediocre. What are you doing RIGHT NOW to fix this?",
            "This is your dopamine system hijacking your prefrontal cortex. You're literally training your brain to choose easy over important. Every time you do this, you're carving neural pathways that make you weaker. Start the task NOW.",
            "You're exhibiting classic self-sabotage behavior - your subconscious is more afraid of success than failure. Every hour you waste is programming yourself for a lifetime of 'what if.' What specific action breaks this cycle in the next 5 minutes?",
            "Loss aversion psychology: You've already invested time planning this. By quitting now, you're not just losing today - you're proving to yourself that your word means nothing. How does it feel to be someone who can't trust themselves?",
            "That's your amygdala talking - the primitive brain that kept cavemen alive but keeps modern humans average. Your rational brain knows what needs to be done. Override the emotion. What's the first concrete step?",
            "You're experiencing cognitive dissonance - the discomfort between who you say you are and what you actually do. The gap is widening. Either change your actions or admit you're not who you claim to be. Which is it?",
            "This is learned helplessness in action. You're conditioning yourself to give up the moment things feel difficult. Psychology shows this pattern spreads to every area of your life. Break it NOW or watch it destroy everything you claim to want.",
            "Your future self is watching this moment. In 5 years, will you remember this as the day you broke through or the day you proved you can't be trusted? The next action you take decides. What is it?"
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
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": DEFAULT_MODEL,
                "messages": messages_for_llm,
                "temperature": 1,
                "max_tokens": 4096, # Adjusted for safety with free models
            }

            response = requests.post(
                OPENROUTER_API_URL, headers=headers, data=json.dumps(data)
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            
            result = response.json()
            return result['choices'][0]['message']['content']
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

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": DEFAULT_MODEL,
                "messages": messages_for_llm,
                "temperature": 1, # Slightly higher temp for more creative pings
                "max_tokens": 4096,
            }

            response = requests.post(
                OPENROUTER_API_URL, headers=headers, data=json.dumps(data)
            )
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content']
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
