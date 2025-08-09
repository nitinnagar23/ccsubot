from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin
from utils.parsers import extract_user
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta
from utils.moderation import execute_punishment
from modules.log_channels.service import log_action

warnings_collection = db["warnings"]
chat_settings_collection = db["chat_settings"]

# --- Core Logic ---
async def _execute_warn_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user, chat_id: int):
    """Executes the punishment when a user exceeds the warn limit."""
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    mode = settings.get("warn_mode", "kick")
    duration_sec = settings.get("warn_mode_duration_seconds", 0)
    
    success, action_string = await execute_punishment(context, chat_id, target_user.id, mode, duration_sec)

    if success:
        action_msg = f"{target_user.mention_html()} has reached the warning limit and has been **{action_string}**."
        await context.bot.send_message(chat_id, action_msg, parse_mode=ParseMode.HTML)
        # Reset warnings after punishment
        warnings_collection.delete_many({"chat_id": chat_id, "user_id": target_user.id})
        # Log the punishment
        log_msg = (f"<b>#WARN_PUNISHMENT</b>\n"
                   f"<b>User:</b> {target_user.mention_html()} (<code>{target_user.id}</code>)\n"
                   f"<b>Action:</b> {action_string.capitalize()}")
        await log_action(context, chat_id, "warns", log_msg)

async def _issue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE, delete_reply: bool, silent: bool):
    """The main logic for issuing a warning."""
    chat_id = await resolve_target_chat_id(update, context)
    chat = await context.bot.get_chat(chat_id)
    warner = update.effective_user
    
    if not update.message.reply_to_message:
        await update.message.reply_text("You need to reply to a user's message to warn them.")
        return

    warned_user = update.message.reply_to_message.from_user
    reason = " ".join(context.args) or "No reason specified."
    
    if await is_user_admin(context, chat_id, warned_user.id):
        await update.message.reply_text("I can't warn an admin.")
        return
    
    warnings_collection.insert_one({
        "chat_id": chat_id, "user_id": warned_user.id, "warner_id": warner.id,
        "reason": reason, "timestamp": datetime.now(timezone.utc)})
    
    if delete_reply: try: await update.message.reply_to_message.delete()
    except: pass
    if silent: try: await update.message.delete()
    except: pass

    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    warn_limit = settings.get("warn_limit", 3)
    warn_time_sec = settings.get("warn_time_seconds", 0)
    
    query = {"chat_id": chat_id, "user_id": warned_user.id}
    if warn_time_sec > 0:
        query["timestamp"] = {"$gte": datetime.now(timezone.utc) - timedelta(seconds=warn_time_sec)}
        
    current_warns = warnings_collection.count_documents(query)
    
    # Log the warning itself
    log_msg = (f"<b>#WARN</b>\n"
               f"<b>Admin:</b> {warner.mention_html()} (<code>{warner.id}</code>)\n"
               f"<b>User:</b> {warned_user.mention_html()} (<code>{warned_user.id}</code>)\n"
               f"<b>Reason:</b> {reason}\n<b>Total Warnings:</b> {current_warns}/{warn_limit}")
    await log_action(context, chat_id, "warns", log_msg)

    if current_warns >= warn_limit:
        await _execute_warn_punishment(update, context, warned_user, chat_id)
    elif not silent:
        await update.message.reply_text(
            f"{warned_user.mention_html()} has been warned. ({current_warns}/{warn_limit})",
            parse_mode=ParseMode.HTML)

# --- Admin Commands ---
@admin_only
async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await _issue_warning(update, context, False, False)
@admin_only
async def dwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await _issue_warning(update, context, True, False)
@admin_only
async def swarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await _issue_warning(update, context, False, True)
    
# ... (Implement /warns, /rmwarn, /resetwarn, /resetallwarns, /warnings, /warnmode, /warnlimit, /warntime as straightforward DB operations) ...
