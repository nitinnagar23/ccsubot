import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Telegram Bot Token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

# List of super admin user IDs from environment variable
# These users will have top-level access to the bot
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
try:
    ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',')]
except ValueError:
    raise ValueError("ADMIN_IDS must be a comma-separated list of integers.
    ")
