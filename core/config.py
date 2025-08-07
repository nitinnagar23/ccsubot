import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# --- Telegram Bot Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

# List of super admin user IDs from environment variable
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
try:
    ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',')]
except (ValueError, AttributeError):
    print("Warning: ADMIN_IDS not found or invalid. No super admins have been set.")
    ADMIN_IDS = []

# --- Database Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("No MONGO_URI found in environment variables!")
