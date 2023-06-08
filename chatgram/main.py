import os

# import NiceGui
from dotenv import load_dotenv
from TGPersonas import TGPersona

# Load .env file
load_dotenv()
print("Starting now...")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Run the bot
tg_persona = TGPersona(TELEGRAM_BOT_TOKEN)
tg_persona.run()
print("hello!")




