import time
from datetime import timedelta
from telegram import Update, User
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta
# Import our new centralized punishment utility
from utils.moderation import execute_punishment
# Import the logging service
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- Helper to get settings ---
def get_flood_settings(chat_id: int):
    return chat_settings_collection.find_one({"_id": chat_id}) or {}

# --- Admin Configuration Commands ---
@admin_only
async def set_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the consecutive message flood limit."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args:
        await update.message.reply_text("You need to specify a number or 'off'.")
        return
        
    arg = args[0].lower()
    if arg in ["off", "no", "0"]:
        limit = 0
        status_msg = "Antiflood has been disabled."
    elif arg.isdigit():
        limit = int(arg)
        if limit < 2:
            await update.message.reply_text("Flood limit must be at least 2.")
            return
        status_msg = f"Antiflood will now trigger after {limit} consecutive messages."
    else:
        await update.message.reply_text("Invalid input. Use a number or 'off'.")
        return

    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"flood_limit": limit}}, upsert=True)
    await update.message.reply_text(status_msg)

@admin_only
async def set_flood_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the action to take when a flood is detected."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args:
        await update.message.reply_text("You need to specify an action type: ban, kick, mute, tban, tmute.")
        return

    mode = args[0].lower()
    duration = timedelta(0)
    
    if mode not in ["ban", "kick", "mute", "tban", "tmute"]:
        await update.message.reply_text(f"Invalid mode: `{mode}`")
        return

    if mode in ["tban", "tmute"]:
        if len(args) < 2:
            await update.message.reply_text(f"You need to specify a duration for {mode} (e.g., 3d, 12h, 30m).")
            return
        duration = parse_duration(args[1])
        if not duration:
            await update.message.reply_text("Invalid duration format. Use 'd', 'h', 'm', or 's'.")
            return

    chat_settings_collection.update_one(
        {"_id": chat_id},
        {"$set": {"flood_mode": mode, "flood_action_duration_seconds": duration.total_seconds()}},
        upsert=True
    )
    
    msg = f"Flood mode has been set to **{mode}**."
    if duration.total_seconds() > 0:
        msg += f" Duration: **{humanize_delta(duration)}**."
        
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# ... (You would add the other config commands like /setfloodtimer, /clearflood, and /flood (status) here following the same pattern) ...

# --- The Core Message Handler ---
async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main handler that checks every message for flood."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or user.is_bot:
        return

    # Exemption check
    if await is_user_admin(context, chat.id, user.id) or is_user_approved(chat.id, user.id):
        return

    settings = get_flood_settings(chat.id)
    limit = settings.get("flood_limit", 0)
    if limit <= 0:
        return
        
    flood_tracker = context.chat_data.setdefault("flood_tracker", {})
    
    if flood_tracker.get("last_user_id") == user.id:
        flood_tracker["count"] += 1
        flood_tracker["messages"].append(update.message.message_id)
    else:
        flood_tracker = {"last_user_id": user.id, "count": 1, "messages": [update.message.message_id]}
    
    context.chat_data["flood_tracker"] = flood_tracker

    if flood_tracker["count"] >= limit:
        await _execute_flood_action(update, context, user, settings, flood_tracker["messages"])
        context.chat_data.pop("flood_tracker", None) # Reset after action

async def _execute_flood_action(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, settings: dict, message_ids: list):
    """Performs the flood action using the centralized moderation utility."""
    chat = update.effective_chat
    mode = settings.get("flood_mode", "kick")
    duration_sec = settings.get("flood_action_duration_seconds", 0)
    
    # Use the centralized punishment function
    success, action_string = await execute_punishment(context, chat.id, user.id, mode, duration_sec)
    
    if success:
        action_msg = f"{user.mention_html()} has been **{action_string}** for flooding."
        await context.bot.send_message(chat.id, action_msg, parse_mode=ParseMode.HTML)
        
        # Log the action
        log_msg = (
            f"<b>#ANTIFLOOD</b>\n"
            f"<b>User:</b> {user.mention_html()} (<code>{user.id}</code>)\n"
            f"<b>Action:</b> {action_string.capitalize()}"
        )
        await log_action(context, chat.id, "bans", log_msg)

        if settings.get("clear_flood", True) and message_ids:
            try:
                await context.bot.delete_messages(chat_id=chat.id, message_ids=message_ids)
            except Exception:
                pass
    else:
        # The punishment failed, maybe due to permissions.
        await context.bot.send_message(chat.id, f"⚠️ Tried to take flood action on {user.mention_html()} but failed: {action_string}")
