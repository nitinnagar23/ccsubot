import time
from datetime import timedelta
from telegram import Update, User
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# --- Local Imports ---
from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta
from utils.moderation import execute_punishment

# --- Service Integrations ---
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- Helper to get settings ---
def get_flood_settings(chat_id: int):
    return chat_settings_collection.find_one({"_id": chat_id}) or {}

# --- Admin Configuration Commands (with Logging) ---
@admin_only
async def set_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the consecutive message flood limit."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args: return
        
    arg = args[0].lower()
    if arg in ["off", "no", "0"]:
        limit, status_msg, log_value = 0, "Antiflood has been disabled.", "Disabled"
    elif arg.isdigit() and int(arg) >= 2:
        limit, status_msg, log_value = int(arg), f"Antiflood will now trigger after {int(arg)} consecutive messages.", str(arg)
    else:
        await update.message.reply_text("Invalid input. Use a number (>=2) or 'off'.")
        return

    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"flood_limit": limit}}, upsert=True)
    await update.message.reply_text(status_msg)

    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> Consecutive Flood Limit\n<b>New Value:</b> {log_value}")
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def set_flood_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the action to take when a flood is detected."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["ban", "kick", "mute", "tban", "tmute"]: return

    mode = args[0].lower()
    duration = parse_duration(args[1]) if len(args) > 1 and mode in ["tban", "tmute"] else timedelta(0)
    
    chat_settings_collection.update_one(
        {"_id": chat_id},
        {"$set": {"flood_mode": mode, "flood_action_duration_seconds": duration.total_seconds()}},
        upsert=True)
    
    msg = f"Flood mode has been set to <b>{mode}</b>."
    log_value = mode.capitalize()
    if duration.total_seconds() > 0:
        human_duration = humanize_delta(duration)
        msg += f" Duration: <b>{human_duration}</b>."
        log_value += f" for {human_duration}"
        
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> Flood Mode\n<b>New Value:</b> {log_value}")
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def set_flood_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the timed flood limit (x messages in y seconds)."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    
    if not args or (len(args) == 1 and args[0].lower() in ['off', 'no']):
        chat_settings_collection.update_one(
            {"_id": chat_id}, {"$set": {"timed_flood_limit": 0, "timed_flood_seconds": 0}}, upsert=True)
        await update.message.reply_text("Timed antiflood has been disabled.")
        log_value = "Disabled"
    elif len(args) == 2 and args[0].isdigit() and int(args[0]) >= 2:
        count = int(args[0])
        duration = parse_duration(args[1])
        if not duration or duration.total_seconds() <= 0:
            await update.message.reply_text("Invalid duration format.")
            return
        chat_settings_collection.update_one(
            {"_id": chat_id}, {"$set": {"timed_flood_limit": count, "timed_flood_seconds": duration.total_seconds()}}, upsert=True)
        log_value = f"{count} messages in {humanize_delta(duration)}"
        await update.message.reply_text(f"Timed antiflood set to trigger after {log_value}.")
    else:
        await update.message.reply_text("Usage: `/setfloodtimer <count> <duration>` (e.g., 10 30s) or 'off'.")
        return
        
    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> Timed Flood\n<b>New Value:</b> {log_value}")
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def clear_flood_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set whether to delete flooding messages."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["yes", "no", "on", "off"]:
        await update.message.reply_text("Please specify `on` or `off`.")
        return

    setting = args[0].lower() in ["yes", "on"]
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"clear_flood": setting}}, upsert=True)
    status = "will now be deleted" if setting else "will be kept"
    await update.message.reply_text(f"Messages that trigger a flood {status}.")
    
    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> Clear Flood Messages\n<b>New Value:</b> {'Enabled' if setting else 'Disabled'}")
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def get_flood_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the current antiflood settings."""
    chat_id = await resolve_target_chat_id(update, context)
    settings = get_flood_settings(chat_id)
    limit = settings.get("flood_limit", 0)
    timed_limit = settings.get("timed_flood_limit", 0)
    timed_seconds = settings.get("timed_flood_seconds", 0)
    mode = settings.get("flood_mode", "kick")
    duration_sec = settings.get("flood_action_duration_seconds", 0)
    duration = timedelta(seconds=duration_sec)
    clear = settings.get("clear_flood", True)

    msg = "🌊 <b>Antiflood Settings</b>\n\n"
    msg += f"• <b>Consecutive Flood</b>: <code>{'OFF' if limit == 0 else f'{limit} messages'}</code>\n"
    msg += f"• <b>Timed Flood</b>: <code>{'OFF' if timed_limit == 0 else f'{timed_limit} messages in {humanize_delta(timedelta(seconds=timed_seconds))}'}</code>\n"
    msg += f"• <b>Action</b>: <code>{mode.upper()}</code>"
    if duration.total_seconds() > 0:
        msg += f" for {humanize_delta(duration)}"
    msg += f"\n• <b>Delete Messages</b>: <code>{'YES' if clear else 'NO'}</code>"
    
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# --- The Core Message Handler ---
async def _execute_flood_action(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, settings: dict, message_ids: list):
    """Performs the flood action using the centralized moderation utility."""
    chat = update.effective_chat
    mode = settings.get("flood_mode", "kick")
    duration_sec = settings.get("flood_action_duration_seconds", 0)
    
    success, action_string = await execute_punishment(context, chat.id, user.id, mode, duration_sec)
    
    if success:
        action_msg = f"{user.mention_html()} has been **{action_string}** for flooding."
        await context.bot.send_message(chat.id, action_msg, parse_mode=ParseMode.HTML)
        
        log_msg = (f"<b>#ANTIFLOOD</b>\n"
                   f"<b>User:</b> {user.mention_html()} (<code>{user.id}</code>)\n"
                   f"<b>Action:</b> {action_string.capitalize()}")
        await log_action(context, chat.id, "bans", log_msg)

        if settings.get("clear_flood", True):
            try: await context.bot.delete_messages(chat_id=chat.id, message_ids=message_ids)
            except: pass
    else:
        await context.bot.send_message(chat.id, f"⚠️ Tried to take flood action on {user.mention_html()} but failed: {action_string}")

async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main handler that checks every message for flood."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or user.is_bot: return

    if await is_user_admin(context, chat.id, user.id) or is_user_approved(chat.id, user.id): return

    settings = get_flood_settings(chat.id)
    now = time.time()
    
    # --- 1. Consecutive Flood Check ---
    limit = settings.get("flood_limit", 0)
    if limit > 0:
        flood_tracker = context.chat_data.setdefault("flood_tracker", {})
        if flood_tracker.get("last_user_id") == user.id:
            flood_tracker["count"] += 1
            flood_tracker["messages"].append(update.message.message_id)
        else:
            flood_tracker = {"last_user_id": user.id, "count": 1, "messages": [update.message.message_id]}
        
        context.chat_data["flood_tracker"] = flood_tracker

        if flood_tracker["count"] >= limit:
            await _execute_flood_action(update, context, user, settings, flood_tracker["messages"])
            context.chat_data.pop("flood_tracker", None)
            return

    # --- 2. Timed Flood Check ---
    timed_limit = settings.get("timed_flood_limit", 0)
    timed_seconds = settings.get("timed_flood_seconds", 0)
    if timed_limit > 0 and timed_seconds > 0:
        timed_tracker = context.chat_data.setdefault("timed_flood_tracker", {})
        user_messages = timed_tracker.setdefault(user.id, [])
        
        user_messages.append({"ts": now, "id": update.message.message_id})
        user_messages = [msg for msg in user_messages if now - msg["ts"] <= timed_seconds]
        
        if len(user_messages) >= timed_limit:
            message_ids = [msg["id"] for msg in user_messages]
            await _execute_flood_action(update, context, user, settings, message_ids)
            timed_tracker.pop(user.id, None)
            
        timed_tracker[user.id] = user_messages
