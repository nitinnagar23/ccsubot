from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# --- Local Imports ---
from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin
from utils.parsers import extract_user
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta
from utils.moderation import execute_punishment

# --- Service Integrations ---
from modules.log_channels.service import log_action
from modules.cleaning_bot_messages.service import schedule_bot_message_deletion

warnings_collection = db["warnings"]
chat_settings_collection = db["chat_settings"]

# --- Core Logic ---
async def _execute_warn_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user, chat_id: int):
    # This function is correct and remains unchanged.
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    mode = settings.get("warn_mode", "kick")
    duration_sec = settings.get("warn_mode_duration_seconds", 0)
    success, action_string = await execute_punishment(context, chat_id, target_user.id, mode, duration_sec)
    if success:
        action_msg = f"{target_user.mention_html()} has reached the warning limit and has been <b>{action_string}</b>."
        sent_message = await context.bot.send_message(chat_id, action_msg, parse_mode=ParseMode.HTML)
        schedule_bot_message_deletion(context, sent_message, "action")
        warnings_collection.delete_many({"chat_id": chat_id, "user_id": target_user.id})
        log_msg = (f"<b>#WARN_PUNISHMENT</b>\n<b>User:</b> {target_user.mention_html()} (<code>{target_user.id}</code>)\n<b>Action:</b> {action_string.capitalize()}")
        await log_action(context, chat_id, "warns", log_msg)

async def _issue_warning(update: Update, context: ContextTypes.DEFAULT_TYPE, delete_reply: bool, silent: bool):
    """The main logic for issuing a warning."""
    chat_id = await resolve_target_chat_id(update, context)
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
    
    # --- SYNTAX FIX APPLIED ---
    # The fragile one-liners have been replaced with standard, robust blocks.
    if delete_reply:
        try:
            await update.message.reply_to_message.delete()
        except Exception:
            pass
    if silent:
        try:
            await update.message.delete()
        except Exception:
            pass

    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    warn_limit = settings.get("warn_limit", 3)
    warn_time_sec = settings.get("warn_time_seconds", 0)
    
    query = {"chat_id": chat_id, "user_id": warned_user.id}
    if warn_time_sec > 0:
        query["timestamp"] = {"$gte": datetime.now(timezone.utc) - timedelta(seconds=warn_time_sec)}
        
    current_warns = warnings_collection.count_documents(query)
    
    log_msg = (f"<b>#WARN</b>\n<b>Admin:</b> {warner.mention_html()} (<code>{warner.id}</code>)\n"
               f"<b>User:</b> {warned_user.mention_html()} (<code>{warned_user.id}</code>)\n"
               f"<b>Reason:</b> {reason}\n<b>Total Warnings:</b> {current_warns}/{warn_limit}")
    await log_action(context, chat_id, "warns", log_msg)

    if current_warns >= warn_limit:
        await _execute_warn_punishment(update, context, warned_user, chat_id)
    elif not silent:
        sent_message = await update.message.reply_text(
            f"{warned_user.mention_html()} has been warned. ({current_warns}/{warn_limit})",
            parse_mode=ParseMode.HTML
        )
        schedule_bot_message_deletion(context, sent_message, "action")

# --- Command Wrappers ---
@admin_only
async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await _issue_warning(update, context, False, False)
@admin_only
async def dwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await _issue_warning(update, context, True, False)
@admin_only
async def swarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await _issue_warning(update, context, False, True)
    
# --- Management and Configuration Commands ---
@admin_only
async def warns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """See a user's warnings."""
    chat_id = await resolve_target_chat_id(update, context)
    target_id, target_name = await extract_user(update, context)
    if not target_id:
        await update.message.reply_text("You need to specify a user to see their warnings.")
        return
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    warn_time_sec = settings.get("warn_time_seconds", 0)
    query = {"chat_id": chat_id, "user_id": target_id}
    time_limit_str = ""
    if warn_time_sec > 0:
        query["timestamp"] = {"$gte": datetime.now(timezone.utc) - timedelta(seconds=warn_time_sec)}
        time_limit_str = f" from the last {humanize_delta(timedelta(seconds=warn_time_sec))}"
    user_warns = list(warnings_collection.find(query).sort("timestamp", -1))
    if not user_warns:
        await update.message.reply_text(f"{target_name} has no active warnings.")
        return
    msg = f"<b>Warnings for {target_name}</b> ({len(user_warns)} total{time_limit_str}):\n\n"
    for i, warn in enumerate(user_warns):
        msg += f"<code>{i+1}</code>: {warn['reason']}\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def rmwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Removes the latest warning from a user."""
    chat_id = await resolve_target_chat_id(update, context)
    target_id, target_name = await extract_user(update, context)
    if not target_id:
        await update.message.reply_text("You need to specify a user to remove a warning from.")
        return
    latest_warn = warnings_collection.find_one_and_delete(
        {"chat_id": chat_id, "user_id": target_id},
        sort=[("timestamp", -1)]
    )
    if latest_warn: await update.message.reply_text(f"Removed the latest warning from {target_name}.")
    else: await update.message.reply_text(f"{target_name} has no warnings to remove.")

@admin_only
async def resetwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resets all warnings for a user."""
    chat_id = await resolve_target_chat_id(update, context)
    target_id, target_name = await extract_user(update, context)
    if not target_id:
        await update.message.reply_text("You need to specify a user to reset warnings for.")
        return
    warnings_collection.delete_many({"chat_id": chat_id, "user_id": target_id})
    await update.message.reply_text(f"Reset all warnings for {target_name}.")

@admin_only
async def resetallwarns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks for confirmation to reset all warnings in the chat."""
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ Yes, reset all warnings", callback_data="warn:resetall_confirm"),
        InlineKeyboardButton("Cancel", callback_data="warn:resetall_cancel")]])
    await update.message.reply_text("Are you sure you want to delete ALL warnings for every user in this chat? This cannot be undone.", reply_markup=keyboard)

async def resetallwarns_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /resetallwarns confirmation."""
    query = update.callback_query
    chat_id = query.message.chat.id
    if not await is_user_admin(context, chat_id, query.from_user.id):
        await query.answer("Only admins can do this.", show_alert=True)
        return
    if query.data.endswith("confirm"):
        warnings_collection.delete_many({"chat_id": chat_id})
        await query.edit_message_text("✅ All warnings in this chat have been reset.")
    else:
        await query.edit_message_text("Action cancelled.")

@admin_only
async def warnings_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gets the chat's current warning settings."""
    chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    limit = settings.get("warn_limit", 3)
    mode = settings.get("warn_mode", "kick")
    duration_sec = settings.get("warn_mode_duration_seconds", 0)
    time_sec = settings.get("warn_time_seconds", 0)
    msg = (f"<b>Warning Settings</b>\n\n"
           f"• <b>Limit</b>: <code>{limit}</code> warnings\n"
           f"• <b>Action</b>: <code>{mode.upper()}</code>")
    if duration_sec > 0: msg += f" for {humanize_delta(timedelta(seconds=duration_sec))}"
    msg += f"\n• <b>Warning Expiration</b>: <code>{'Permanent' if time_sec == 0 else humanize_delta(timedelta(seconds=time_sec))}</code>"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def warnmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the punishment for exceeding the warn limit."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["ban", "kick", "mute", "tban", "tmute"]:
        await update.message.reply_text("Usage: `/warnmode <ban/kick/mute/tban/tmute> [duration]`")
        return
    mode = args[0].lower()
    duration = parse_duration(args[1]) if len(args) > 1 else None
    if mode in ["tban", "tmute"] and not duration:
        await update.message.reply_text("You must provide a duration for temporary actions.")
        return
    chat_settings_collection.update_one(
        {"_id": chat_id},
        {"$set": {"warn_mode": mode, "warn_mode_duration_seconds": duration.total_seconds() if duration else 0}},
        upsert=True)
    await update.message.reply_text(f"Warning punishment is now set to {mode}.")

@admin_only
async def warntime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets how long warnings last before expiring."""
    chat_id = await resolve_target_chat_id(update, context)
    if not context.args:
        await update.message.reply_text("Usage: `/warntime <duration>` (e.g., 4w, 7d). Use 'off' for permanent warnings.")
        return
    duration_str = context.args[0].lower()
    if duration_str == 'off':
        duration_seconds, msg = 0, "Warnings are now permanent."
    else:
        duration = parse_duration(duration_str)
        if not duration:
            await update.message.reply_text("Invalid duration format.")
            return
        duration_seconds, msg = duration.total_seconds(), f"Warnings will now expire after {humanize_delta(duration)}."
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"warn_time_seconds": duration_seconds}}, upsert=True)
    await update.message.reply_text(msg)
