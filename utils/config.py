import os

def get_bot_owners() -> list[int]:
    """Gets a list of bot owner user IDs from environment variables."""
    owners_str = os.environ.get("BOT_OWNERS", "")
    if not owners_str:
        print("⚠️ BOT_OWNERS secret is not set. Owner-only commands will not work.")
        return []
    
    try:
        return [int(owner_id.strip()) for owner_id in owners_str.split(',')]
    except ValueError:
        print("⚠️ BOT_OWNERS secret contains non-integer values.")
        return []

# --- Load all secrets and configurations on startup ---
BOT_OWNERS = get_bot_owners()
DONATION_URL = os.environ.get("DONATION_URL")
DONATION_TEXT = os.environ.get("DONATION_TEXT", "The bot owner has not set up a donation link.")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DEV_LOG_CHANNEL = os.environ.get("DEV_LOG_CHANNEL")
SUPPORT_GROUP_URL = os.environ.get("SUPPORT_GROUP_URL")
