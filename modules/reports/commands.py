import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.permissions import is_user_admin
from utils.context import resolve_target_chat_id
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- Core Report Logic ---
async def _execute_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The central logic for handling a report request."""
    chat_id = await resolve_target_chat_id(update, context)
    chat = update.effective_chat
    reporter = update.effective_user

    if not update.message.reply_to_message:
        return # Silently ignore if not a reply

    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    if not settings.get("reports_enabled", True): # Enabled by default
        return

    reported_message = update.message.reply_to_message
    reported_user = reported_message.from_user
    
    # Permission checks: admins can't report or be reported
    if await is_user_admin(context, chat_id, reporter.id) or await is_user_admin(context, chat_id, reported_user.id):
        return

    try:
        admins = await context.bot.get_chat_administrators(chat_id)
    except Exception as e:
        print(f"Could not fetch admins for report in chat {chat_id}: {e}")
        return
        
    admin_mentions = " ".join([admin.user.mention_html() for admin in admins if not admin.user.is_bot])
    
    if not admin_mentions: return # No human admins to notify

    text = (f"❗️ <b>Admin Alert</b> ❗️\n"
            f"{reporter.mention_html()} has reported a <a href='{reported_message.link}'>message</a> from {reported_user.mention_html()}.\n\n"
            f"Calling for review: {admin_mentions}")
    
    # Reply to the reported message for context
    await reported_message.reply_text(text, parse_mode=ParseMode.HTML)
    
    # Log the action
    log_msg = (f"<b>#REPORT</b>\n"
               f"<b>Reporter:</b> {reporter.mention_html()} (<code>{reporter.id}</code>)\n"
               f"<b>Reported User:</b> {reported_user.mention_html()} (<code>{reported_user.id}</code>)\n"
               f"<b>Reported Message:</b> <a href='{reported_message.link}'>Link</a>")
    await log_action(context, chat_id, "reports", log_msg)

    # Clean up the triggering command (/report or @admin)
    try: await update.message.delete()
    except: pass

# --- Handlers ---
@check_disabled
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /report command."""
    await _execute_report(update, context)

async def admin_mention_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for @admin mentions."""
    if re.search(r'(?i)@admin', update.message.text):
        await _execute_report(update, context)

# --- Admin Configuration Command ---
@admin_only
async def toggle_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable or disable the user reporting system."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    current_status = settings.get("reports_enabled", True)

    if not args:
        status_text = "ENABLED" if current_status else "DISABLED"
        await update.message.reply_text(f"User reports are currently <b>{status_text}</b>.", parse_mode=ParseMode.HTML)
        return

    enabled = args[0].lower() in ["on", "yes"]
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"reports_enabled": enabled}}, upsert=True)
    status_text = "enabled" if enabled else "disabled"
    await update.message.reply_text(f"✅ User reports have been <b>{status_text}</b>.", parse_mode=ParseMode.HTML)
