import os
from dotenv import load_dotenv

load_dotenv()

# Required config
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

OWNER_ID = [int(x) for x in os.getenv("OWNER_ID", "123456789").split()]
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "your_support_chat")
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBotUsername")

# Optional config
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))
ENABLE_UPTIME = os.getenv("ENABLE_UPTIME", "true").lower() == "true"
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
WORKERS = int(os.getenv("WORKERS", "4"))

# Command prefixes
COMMAND_PREFIXES = ["/", "!"]
