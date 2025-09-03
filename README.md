# **Telegram Persona Bot**

A highly configurable Telegram bot designed for personal use, capable of adopting various personas to interact with you, providing scheduled reminders, and maintaining conversation history.

\!

## **Features**

* **Multiple Personas**: Switch between different personalities like a motivational coach, a concise assistant, or an accountability partner.  
* **Conversation Memory**: Remembers the last 50 messages to provide contextually relevant responses.  
* **Scheduled Pings**: Configure daily reminders and check-ins at specific times.  
* **Easy Configuration**: Set up and customize the bot using environment variables.  
* **Data Persistence**: Uses a SQLite database to store settings, conversation history, and schedules.  
* **Optional LLM Integration**: Enhance responses with a powerful language model using the Groq API.  

## **How It Works**

The bot is built using Python and the python-telegram-bot library. It's designed to be a single-user bot, restricted to the owner's Telegram ID for private use. Here’s a quick overview of its architecture:

* **main.py**: The entry point of the application. It initializes the bot, loads handlers, and starts the scheduler.  
* **bot/handlers.py**: Contains all the command and message handlers that define the bot's behavior.  
* **bot/personas.py**: Manages the different personalities the bot can adopt. It can use predefined templates or an external LLM for generating responses.  
* **bot/scheduler.py**: Handles the scheduling of pings using APScheduler.  
* **database/db\_utils.py**: Manages all interactions with the SQLite database, including storing messages and user settings.

## **Getting Started**

Follow these instructions to set up and run the bot on your local machine.

### **Prerequisites**

* Python 3.8 or higher  
* A Telegram Bot Token (get one from [BotFather](https://t.me/botfather))  
* Your Telegram User ID (get it from a bot like [@userinfobot](https://t.me/userinfobot))  
* (Optional) A Groq API key for LLM integration.

### **Local Setup**

1. **Clone the repository:**  
   git clone \[https://github.com/your-username/telegram-persona-bot.git\](https://github.com/your-username/telegram-persona-bot.git)  
   cd telegram-persona-bot

2. **Create and activate a virtual environment:**  
   python \-m venv venv  
   source venv/bin/activate  \# On Windows, use \`venv\\Scripts\\activate\`

3. **Install the required dependencies:**  
   pip install \-r requirements.txt

4. Configure your environment variables:  
   Create a file named .env in the root directory and add the following, replacing the placeholder values with your own:  
   \# .env  
   TELEGRAM\_BOT\_TOKEN="YOUR\_TELEGRAM\_BOT\_TOKEN"  
   OWNER\_TELEGRAM\_ID="YOUR\_TELEGRAM\_ID"  
   TIMEZONE="UTC"  \# e.g., "America/New\_York", "Europe/London"  
   DATABASE\_PATH="bot\_data.db"

   \# Optional: For LLM integration  
   GROQ\_API\_KEY="YOUR\_GROQ\_API\_KEY"

5. **Run the bot:**  
   python \-m src.main

   Your bot should now be running and responsive on Telegram\!

## **Usage**

You can interact with the bot using the following commands in your private chat:

* /start: Initializes the bot and shows a welcome message with available commands.  
* /personas: Lists all available personas you can switch to.  
* /set\_persona \<name\>: Switches the bot's personality.  
  * Example: /set\_persona motivational  
* /set\_times \<HH:MM\> \<HH:MM\> ...: Sets the daily times for scheduled pings.  
  * Example: /set\_times 09:00 15:30 21:00  
* /memory\_clear: Clears the bot's conversation history.  
* /export\_memory: Exports the conversation history as a CSV file.

Any message that is not a command will be treated as part of the conversation, and the bot will respond based on its current persona.


## **Project Structure**

.  
├── .gitignore  
├── README.md  
├── requirements.txt  
├── schema.sql  
└── src  
    ├── \_\_init\_\_.py  
    ├── bot  
    │   ├── \_\_init\_\_.py  
    │   ├── handlers.py  
    │   ├── memory.py  
    │   ├── personas.py  
    │   └── scheduler.py  
    ├── database  
    │   ├── \_\_init\_\_.py  
    │   └── db\_utils.py  
    └── main.py

## **Contributing**

Contributions, issues, and feature requests are welcome\! Feel free to check the [issues page](https://www.google.com/search?q=https://github.com/your-username/telegram-persona-bot/issues).