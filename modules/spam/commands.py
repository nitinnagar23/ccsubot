from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta

chat_settings_collection = db["chat_settings"]

@admin_only
async def toggle_spam_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles the Spam Guard system on or off."""
    chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    new_status = not settings.get("spam_guard_enabled", False)
    
    chat_settings_collection.update_one(
        {"_id": chat_id}, {"$set": {"spam_guard_enabled": new_status}}, upsert=True
    )
    status = "enabled" if new_status else "disabled"
    await update.message.reply_text(f"🛡️ Spam Guard has been <b>{status}</b>.", parse_mode=ParseMode.HTML)

@admin_only
async def set_quarantine_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the quarantine duration for new members."""
    chat_id = await resolve_target_chat_id(update, context)
    duration_str = context.args[0] if context.args else ""
    if not duration_str:
        await update.message.reply_text("Usage: `/setquarantine <duration>` (e.g., 24h, 30m). Use 'off' to disable.")
        return

    if duration_str.lower() == 'off':
        duration_seconds = 0
        msg = "New user quarantine has been disabled."
    else:
        duration = parse_duration(duration_str)
        if not duration or duration.total_seconds() < 0:
            await update.message.reply_text("Invalid duration format.")
            return
        duration_seconds = duration.total_seconds()
        msg = f"New members will now be restricted for <b>{humanize_delta(duration)}</b> after joining."

    chat_settings_collection.update_one(
        {"_id": chat_id}, {"$set": {"quarantine_seconds": duration_seconds}}, upsert=True
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
