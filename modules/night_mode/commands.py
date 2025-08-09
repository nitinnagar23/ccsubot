import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]

# --- Core Logic: Time Check ---
def is_night_mode_active(settings: dict) -> tuple[bool, str]:
    """
    Checks if night mode should be currently active based on settings.
    Returns (isActive, reasonString).
    """
    # 1. Check for manual override
    if "nightmode_enabled" in settings:
        status = settings["nightmode_enabled"]
        return status, "Manual Override"

    # 2. Check schedule if no override is set
    start_str = settings.get("nightmode_schedule_start")
    end_str = settings.get("nightmode_schedule_end")
    tz_str = settings.get("nightmode_timezone", "UTC")

    if not start_str or not end_str:
        return False, "Not Configured"

    try:
        timezone = pytz.timezone(tz_str)
        now = datetime.now(timezone).time()
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        
        # Handle overnight schedules (e.g., 23:00 to 06:00)
        if start_time > end_time:
            is_active = now >= start_time or now < end_time
        else:
            is_active = start_time <= now < end_time
        
        return is_active, "Scheduled"
    except Exception as e:
        print(f"Error checking night mode time: {e}")
        return False, "Error"

# --- Core Listener ---
async def check_night_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The MessageHandler that checks and deletes restricted messages."""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not chat or not user or not message or user.is_bot: return
        
    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    is_active, _ = is_night_mode_active(settings)
    if not is_active: return

    # Exemption Check
    is_exempt = (
        await is_user_admin(context, chat.id, user.id) or
        is_user_approved(chat.id, user.id) or
        user.id in settings.get("nightmode_whitelist", [])
    )
    if is_exempt: return
        
    # Check for restricted content types
    blocked_types = settings.get("nightmode_blocked_types", [])
    should_delete = False
    if "photo" in blocked_types and message.photo: should_delete = True
    elif "video" in blocked_types and message.video: should_delete = True
    elif "sticker" in blocked_types and message.sticker: should_delete = True
    elif "animation" in blocked_types and message.animation: should_delete = True
    elif message.entities or message.caption_entities:
        for entity in (message.entities or message.caption_entities):
            if entity.type in ['url', 'text_link'] and "link" in blocked_types:
                should_delete = True
                break
    
    if should_delete:
        try: await message.delete()
        except Exception: pass

# --- Admin Commands ---
@admin_only
async def nightmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually enables/disables or schedules night mode."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    
    if not args:
        await update.message.reply_text("Usage: `/nightmode on/off` or `/nightmode <start_HH:MM> <end_HH:MM>`")
        return
    
    if args[0].lower() == "on":
        chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"nightmode_enabled": True}}, upsert=True)
        await update.message.reply_text("🌙 Night mode has been manually **enabled**.", parse_mode=ParseMode.HTML)
    elif args[0].lower() == "off":
        chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"nightmode_enabled": False}}, upsert=True)
        await update.message.reply_text("☀️ Night mode has been manually **disabled**.", parse_mode=ParseMode.HTML)
    elif len(args) == 2:
        try:
            start_time = datetime.strptime(args[0], "%H:%M").strftime("%H:%M")
            end_time = datetime.strptime(args[1], "%H:%M").strftime("%H:%M")
            chat_settings_collection.update_one(
                {"_id": chat_id},
                {"$set": {"nightmode_schedule_start": start_time, "nightmode_schedule_end": end_time},
                 "$unset": {"nightmode_enabled": ""}}, # Remove manual override
                upsert=True)
            await update.message.reply_text(f"✅ Night mode scheduled from **{start_time}** to **{end_time}**.")
        except ValueError:
            await update.message.reply_text("Invalid time format. Please use HH:MM (e.g., 23:00).")
    else:
        await update.message.reply_text("Invalid syntax.")

@admin_only
async def nightmode_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the current night mode status and configuration."""
    chat_id = await resolve_target_chat_id(update, context)
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    
    is_active, reason = is_night_mode_active(settings)
    status_msg = "🌙 **Night Mode Status**\n\n"
    status_msg += f"Current Status: **{'ACTIVE' if is_active else 'INACTIVE'}** (`{reason}`)\n"
        
    start = settings.get("nightmode_schedule_start", "Not set")
    end = settings.get("nightmode_schedule_end", "Not set")
    tz = settings.get("nightmode_timezone", "UTC (default)")
    
    status_msg += f"Schedule: `{start}` - `{end}` (`{tz}`)\n"
    await update.message.reply_text(status_msg, parse_mode=ParseMode.HTML)

@admin_only
async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the timezone for the chat."""
    chat_id = await resolve_target_chat_id(update, context)
    tz_str = context.args[0] if context.args else ""
    try:
        pytz.timezone(tz_str)
        chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"nightmode_timezone": tz_str}}, upsert=True)
        await update.message.reply_text(f"✅ Timezone set to `{tz_str}`.")
    except pytz.UnknownTimeZoneError:
        await update.message.reply_text("Invalid timezone. Please provide a valid TZ database name (e.g., `Asia/Kolkata`, `Europe/London`, `UTC`).")
