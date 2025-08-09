from telegram import Update, Message
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY
from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]
CLEAN_MSG_TIMEOUT = 300  # 5 minutes in seconds
VALID_TYPES = ["all", "action", "filter", "note"]
TYPE_DESCRIPTIONS = {
    "action": "Moderation action messages (ban, mute, etc.).",
    "filter": "Replies sent by the Filters module.",
    "note": "Replies sent by the Notes module.",
    "all": "All of the above supported message types.",
}

# --- Core Logic: Job Queue Callback and Public Helper ---

async def _delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    """The job that gets executed by the JobQueue to delete a message."""
    job_data = context.job.data
    try:
        await context.bot.delete_message(chat_id=job_data['chat_id'], message_id=job_data['message_id'])
    except BadRequest:
        # Message might have been deleted manually already. Safe to ignore.
        pass

def schedule_bot_message_deletion(context: ContextTypes.DEFAULT_TYPE, message: Message, category: str):
    """
    Public helper function for other modules to call.
    Checks settings and schedules a message for deletion if required.
    """
    if not message: return
    
    settings = chat_settings_collection.find_one({"_id": message.chat.id}) or {}
    clean_types = settings.get("clean_bot_msg_settings", [])
    
    if "all" in clean_types or category in clean_types:
        context.job_queue.run_once(
            _delete_message_job,
            CLEAN_MSG_TIMEOUT,
            data={'chat_id': message.chat.id, 'message_id': message.message_id},
            name=f"del_{message.chat.id}_{message.message_id}"
        )

# --- Admin Commands ---

@admin_only
async def set_clean_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets which bot message types to clean."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which message types to clean. Use `/cleanmsgtypes` to see options.")
        return

    invalid_types = [arg for arg in args if arg not in VALID_TYPES]
    if invalid_types:
        await update.message.reply_text(f"Invalid type(s): {', '.join(invalid_types)}. Use `/cleanmsgtypes` to see options.")
        return

    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$addToSet": {"clean_bot_msg_settings": {"$each": args}}},
        upsert=True
    )
    await update.message.reply_text(f"✅ Bot messages of type `{'`, `'.join(args)}` will be deleted after 5 minutes.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def keep_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets which bot message types to stop cleaning."""
    target_chat_id = await resolve_target_chat_id(update, context)
    args = [arg.lower() for arg in context.args]
    if not args:
        await update.message.reply_text("You need to specify which message types to keep.")
        return
        
    chat_settings_collection.update_one(
        {"_id": target_chat_id},
        {"$pullAll": {"clean_bot_msg_settings": args}},
    )
    await update.message.reply_text(f"✅ Bot messages of type `{'`, `'.join(args)}` will no longer be automatically deleted.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def list_clean_msg_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists the current cleaning settings for bot messages."""
    target_chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": target_chat_id}) or {}
    cleaned_types = settings.get("clean_bot_msg_settings", [])
    
    msg = "<b>Current bot message cleaning settings:</b>\n<i>Messages are deleted after 5 minutes.</i>\n\n"
    for type_key, type_desc in TYPE_DESCRIPTIONS.items():
        status = "✅ Cleaning" if type_key in cleaned_types else "❌ Keeping"
        msg += f"• <code>{type_key}</code>: {status}\n<i>{type_desc}</i>\n"
        
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
