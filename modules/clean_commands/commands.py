import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from bot_core.registry import COMMAND_REGISTRY
from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]
VALID_TYPES = ["all", "admin", "user", "other"]

# --- Core Listener ---
async def clean_command_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listens for and cleans commands based on chat settings."""
    chat = update.effective_chat
    if not chat:
        return

    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    clean_types = settings.get("clean_command_settings", [])
    
    if not clean_types:
        return

    # Eagerly delete if 'all' is set
    if "all" in clean_types:
        try:
            await update.message.delete()
        except BadRequest:
            pass # Bot may not have delete permissions
        return

    # Extract command from message text (e.g., /ban@YourBot -> ban)
    command_match = re.match(r"[!/](\w+)", update.message.text)
    if not command_match:
        return
    command = command_match.group(1).lower()

    category_to_clean = None
    if command in COMMAND_REGISTRY:
        # Command is known to our bot, find its category
        category_to_clean = COMMAND_REGISTRY[command].get("category", "user")
    else:
        # Command is not in our registry, so it's for another bot or invalid
        category_to_clean = 'other'

    if category_to_clean in clean_types:
        try:
            await update.message.delete()
        except BadRequest:
            pass

# --- Admin Commands ---
@admin_only
async def set_clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets which command types to clean."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which command types to clean. Use `/cleancommandtypes` to see options.")
        return

    invalid_types = [arg for arg in args if arg not in VALID_TYPES]
    if invalid_types:
        await update.message.reply_text(f"Invalid type(s): {', '.join(invalid_types)}. Use `/cleancommandtypes` to see options.")
        return

    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$addToSet": {"clean_command_settings": {"$each": args}}},
        upsert=True
    )
    await update.message.reply_text(f"✅ Now cleaning commands of type: `{'`, `'.join(args)}`.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def keep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets which command types to stop cleaning."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which command types to keep.")
        return
        
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$pullAll": {"clean_command_settings": args}},
    )
    await update.message.reply_text(f"✅ No longer cleaning commands of type: `{'`, `'.join(args)}`.", parse_mode=ParseMode.MARKDOWN_V2)
    
@admin_only
async def list_clean_command_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists the current cleaning settings."""
    target_chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": target_chat_id}) or {}
    cleaned_types = settings.get("clean_command_settings", [])
    
    msg = "<b>Current command cleaning settings:</b>\n\n"
    for cmd_type in VALID_TYPES:
        status = "✅ Cleaning" if cmd_type in cleaned_types else "❌ Keeping"
        msg += f"• <code>{cmd_type}</code>: {status}\n"
        
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
