from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]

# --- Constants for Validation and Help Text ---
SERVICE_TYPES = {
    "all": "All service messages.",
    "join": "When a new user joins or is added.",
    "leave": "When a user leaves or is removed.",
    "photo": "When the chat photo or background is changed.",
    "title": "When the chat or a topic title is changed.",
    "pin": "When a new message is pinned.",
    "videochat": "When a video chat action occurs (start, end, etc.).",
    "other": "Miscellaneous items (boosts, payments, proximity alerts, etc.).",
}

# --- Core Listener ---
async def clean_service_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listens for and cleans service messages."""
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message:
        return

    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    clean_types = settings.get("clean_service_settings", [])
    
    if not clean_types:
        return

    should_delete = False
    
    if "all" in clean_types:
        should_delete = True
    elif message.new_chat_members and "join" in clean_types:
        should_delete = True
    elif message.left_chat_member and "leave" in clean_types:
        should_delete = True
    elif (message.new_chat_photo or message.delete_chat_photo) and "photo" in clean_types:
        should_delete = True
    elif message.new_chat_title and "title" in clean_types:
        should_delete = True
    elif message.pinned_message and "pin" in clean_types:
        should_delete = True
    elif (message.video_chat_started or message.video_chat_ended or 
          message.video_chat_scheduled or message.video_chat_members_invited) and "videochat" in clean_types:
        should_delete = True
    elif "other" in clean_types:
        # This acts as a catch-all for any other status update not specifically handled above
        should_delete = True
        
    if should_delete:
        try:
            await message.delete()
        except BadRequest:
            # Bot might not have delete permissions, or message is too old.
            pass

# --- Admin Commands ---
@admin_only
async def set_clean_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets which service message types to clean."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which service types to clean. Use `/cleanservicetypes` to see options.")
        return

    # Handle simple on/off for 'all'
    if len(args) == 1 and args[0] in ["on", "yes"]:
        args = ["all"]
    elif len(args) == 1 and args[0] in ["off", "no"]:
        await keep_service(update, context)
        return

    invalid_types = [arg for arg in args if arg not in SERVICE_TYPES]
    if invalid_types:
        await update.message.reply_text(f"Invalid type(s): {', '.join(invalid_types)}. Use `/cleanservicetypes` to see options.")
        return

    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$addToSet": {"clean_service_settings": {"$each": args}}},
        upsert=True
    )
    await update.message.reply_text(f"✅ Now cleaning service messages of type: `{'`, `'.join(args)}`.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def keep_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets which service message types to stop cleaning."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which service types to keep.")
        return
        
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$pullAll": {"clean_service_settings": args}},
    )
    await update.message.reply_text(f"✅ No longer cleaning service messages of type: `{'`, `'.join(args)}`.", parse_mode=ParseMode.MARKDOWN_V2)
    
@admin_only
async def list_clean_service_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists the current cleaning settings for service messages."""
    target_chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": target_chat_id}) or {}
    cleaned_types = settings.get("clean_service_settings", [])
    
    msg = "<b>Current service message cleaning settings:</b>\n\n"
    for type_key, type_desc in SERVICE_TYPES.items():
        status = "✅ Cleaning" if type_key in cleaned_types else "❌ Keeping"
        msg += f"• <code>{type_key}</code>: {status}\n<i>{type_desc}</i>\n"
        
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
