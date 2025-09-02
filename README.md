# Telegram Persona Bot

A Telegram bot that can simulate different personas and maintain conversations with users.

## Features
- Multiple persona support
- Short-term memory for contextual conversations
- Scheduled pings and reminders
- PostgreSQL database for persistence

## Setup
1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the database:
   - Create a PostgreSQL database
   - Run schema.sql to set up tables
   - Configure .env with your database URL

4. Configure environment variables:
   - Copy .env.example to .env
   - Fill in your Telegram bot token
   - Add your OpenAI API key

5. Run the bot:
   ```
   python -m src.main
   ```

## Development
- `src/bot/`: Contains core bot logic
- `src/database/`: Database utilities
- `src/main.py`: Application entry point

## Deployment
Use render.yaml for deploying to Render.com