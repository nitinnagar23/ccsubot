import logging
import asyncio
from pyrogram import Client
from pyrogram.handlers import MessageHandler
from config import API_ID, API_HASH, BOT_TOKEN
from utils.database import init_db
from services.logger import setup_logger
from utils.helpers import is_owner
from modules import load_all_modules
from utils.startup import startup_check

# Set up logging
logger = setup_logger()
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Create the bot client
bot = Client(
    "modular_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4,
    plugins=dict(root="bot/modules"),
)

# Main startup function
async def main():
    await init_db()
    await startup_check(bot)
    logger.info("Loading modules...")
    load_all_modules()
    await bot.start()
    me = await bot.get_me()
    logger.info(f"Bot started as @{me.username} (ID: {me.id})")
    print("Bot is running. Press Ctrl+C to stop.")
    await idle()
    await bot.stop()
    logger.info("Bot stopped.")

# Graceful shutdown support
from pyrogram.idle import idle

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
