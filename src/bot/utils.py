# src/bot/utils.py
import logging
import os
import requests
import urllib.parse

logger = logging.getLogger(__name__)

def send_to_alexa(message_text: str):
    """
    Sends a message to your Alexa device via Voice Monkey.
    """
    token = os.getenv("VOICE_MONKEY_TOKEN")
    device_id = os.getenv("VOICE_MONKEY_DEVICE_ID")

    if not token or not device_id:
        logger.warning("Voice Monkey token or device ID not set in environment variables.")
        return

    # URL-encode the message to handle special characters and spaces
    encoded_message = urllib.parse.quote(message_text)

    # Construct the full API URL
    api_url = f"https://api-v2.voicemonkey.io/announcement?token={token}&device={device_id}&text={encoded_message}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        logger.info("Successfully sent message to Alexa via Voice Monkey.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending to Voice Monkey: {e}")