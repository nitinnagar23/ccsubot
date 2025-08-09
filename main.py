import os
import logging
import importlib
import pathlib
import traceback
import html
import json
import asyncio
import nest_asyncio  # --- Solves the event loop conflict

from telegram import Update
from telegram.ext import ApplicationBuilder, PicklePersistence, ContextTypes
from telegram.constants import ParseMode

from keep_alive import keep_alive

# --- Apply the patch to allow nested event loops in Replit ---
nest_asyncio.apply()

# --- Bot-wide Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Error Handler for Developer Logging ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Logs errors and sends a detailed message to the developer log channel."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    DEV_LOG_CHANNEL = os.environ.get("DEV_LOG_CHANNEL")
    if not DEV_LOG_CHANNEL:
        print("DEV_LOG_CHANNEL not set. Cannot send error log.")
        return

    # Format the traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n\n"
        f"<b>Update:</b>\n<pre>{html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"
        f"<b>Context Chat Data:</b>\n<pre>{html.escape(str(context.chat_data))}</pre>\n\n"
        f"<b>Context User Data:</b>\n<pre>{html.escape(str(context.user_data))}</pre>\n\n"
        f"<b>Traceback:</b>\n<pre>{html.escape(tb_string)}</pre>"
    )
    
    # Split the message into chunks if it's too long for a single Telegram message
    for i in range(0, len(message), 4096):
        try:
            await context.bot.send_message(
                chat_id=DEV_LOG_CHANNEL, text=message[i:i+4096], parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send error log to developer channel: {e}")


# --- Main Bot Function ---
async def main():
    """Start the bot."""
    logger.info("Starting bot...")

    TOKEN = os.environ.get('BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables!")
        return
        
    # Create a persistence object to save jobs across restarts
    persistence = PicklePersistence(filepath="bot_persistence")

    # Build the application with persistence and error handling
    application = ApplicationBuilder().token(TOKEN).persistence(persistence).build()
    application.add_error_handler(error_handler)
    
    logger.info("Telegram application built.")

    # --- Dynamic Module Loader (Package-based) ---
    modules_path = pathlib.Path("modules")
    for module_init_file in modules_path.glob("*/__init__.py"):
        module_name = ".".join(module_init_file.parts[:-1])
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "load_module"):
                module.load_module(application)
                logger.info(f"✅ Loaded module package: {module_name}")
            else:
                logger.warning(f"⚠️ Module package {module_name} is missing 'load_module'.")
        except Exception as e:
            logger.error(f"❌ Failed to load module package {module_name}: {e}")

    logger.info("Bot is running...")
    await application.run_polling()


if __name__ == '__main__':
    keep_alive()
    asyncio.run(main())
