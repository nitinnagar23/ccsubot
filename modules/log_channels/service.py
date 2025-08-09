from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]

# --- Constants for Validation and Help Text ---
LOG_CATEGORIES = {
    "bans": "Bans, mutes, kicks, and unbans/unmutes.",
    "warns": "Warnings issued and removed.",
    "notes": "Notes being saved and cleared.",
    "purges": "Messages being purged.",
    "reports": "User reports made with /report or @admin.",
    "settings": "Changes to any bot setting (e.g., /setflood).",
    "joins": "New users joining the chat.",
    "leaves": "Users leaving or being kicked from the chat.",
}

# --- The Public Logging Service ---
async def log_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, category: str, log_message: str):
    """
    The central logging function for other modules to call.
    Checks settings and sends a message to the log channel if required.
    """
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    log_channel_id = settings.get("log_channel_id")
    log_cats = settings.get("log_categories", [])
    
    if log_channel_id and category in log_cats:
        try:
            await context.bot.send_message(
                chat_id=log_channel_id,
                text=log_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except BadRequest as e:
            print(f"Failed to send log to {log_channel_id}: {e.message}")
            # Optional: unset the log channel here to prevent further errors.

# --- Setup Handlers ---
async def setlog_command_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provides instructions on how to set the log channel."""
    # This command is meant to be sent in the channel itself.
    if update.effective_chat.type == "channel":
        await update.message.reply_text(
            "✅ This channel is now ready to be a log channel. Forward this message to the group you wish to log."
        )
    else:
        await update.message.reply_text("This command should be used in the channel you want to set for logging.")


@admin_only
async def handle_setlog_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the forwarded /setlog message to link a group and channel."""
    chat = update.effective_chat
    forwarded_from = update.message.forward_from_chat

    if not forwarded_from or forwarded_from.type != 'channel':
        await update.message.reply_text("Please forward the `/setlog` message from your desired log channel.")
        return

    log_channel_id = forwarded_from.id
    
    try:
        me_member = await context.bot.get_chat_member(log_channel_id, context.bot.id)
        if not me_member.can_post_messages:
            raise BadRequest("Cannot post messages")
    except BadRequest:
        await update.message.reply_text("I can't post in that channel. Please make sure I am an admin with 'Post Messages' permission there.")
        return

    chat_settings_collection.update_one(
        {"_id": chat.id},
        {"$set": {"log_channel_id": log_channel_id}},
        upsert=True
    )
    await context.bot.send_message(log_channel_id, f"✅ This channel has been set as the log channel for: <b>{chat.title}</b>.", parse_mode=ParseMode.HTML)
    await update.message.reply_text(f"✅ Successfully set <b>{forwarded_from.title}</b> as the log channel.", parse_mode=ParseMode.HTML)

# --- Admin Commands ---
@admin_only
async def unsetlog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unsets the log channel for the chat."""
    chat_id = await resolve_target_chat_id(update, context)
    chat_settings_collection.update_one({"_id": chat_id}, {"$unset": {"log_channel_id": ""}})
    await update.message.reply_text("✅ Log channel has been unset.")

# ... (Implement /log, /nolog, /logcategories following the same patterns) ...
