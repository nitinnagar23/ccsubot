import os
import logging
import importlib
import pathlib
import traceback
import html
import json
import asyncio
import nest_asyncio

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, PicklePersistence, ContextTypes
from telegram.constants import ParseMode

from keep_alive import keep_alive

# Apply the patch to allow nested event loops in Replit/Render
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

    # Build the message using html.escape for safety
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"<b>An exception was raised:</b>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>\n\n"
        f"<b>Full Update:</b>\n"
        f"<pre>{html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>"
    )
    
    # Split the message into chunks if it's too long
    for i in range(0, len(message), 4096):
        try:
            await context.bot.send_message(
                chat_id=DEV_LOG_CHANNEL, text=message[i:i+4096], parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send error log to developer channel: {e}")

# --- Graceful Shutdown Function ---
async def post_shutdown(application: Application):
    """This function is called after the bot is stopped."""
    logger.info("Bot has been shut down. Persistence should be saved.")


# --- Main Bot Function ---
async def main():
    """Start the bot."""
    logger.info("Starting bot...")

    TOKEN = os.environ.get('BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables!")
        return
        
    persistence = PicklePersistence(filepath="bot_persistence")

    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .persistence(persistence)
        .post_shutdown(post_shutdown) # Register the graceful shutdown function
        .build()
    )
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
