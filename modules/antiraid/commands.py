import time
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta
from utils.moderation import execute_punishment
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- Helper function to get settings ---
def get_raid_settings(chat_id: int):
    defaults = {
        "manual_antiraid_until": None,
        "raid_duration_seconds": 6 * 3600,  # 6 hours
        "raid_action_duration_seconds": 1 * 3600,  # 1 hour
        "auto_antiraid_trigger": 0,
    }
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    defaults.update(settings)
    return defaults

# --- Admin Configuration Commands ---
@admin_only
async def antiraid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles antiraid mode on or off."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    settings = get_raid_settings(chat_id)
    
    expiry_time = None
    msg = ""

    if args and args[0].lower() in ["off", "no"]:
        expiry_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        msg = "✅ AntiRaid has been manually disabled."
    else:
        duration_str = args[0] if args else None
        duration = parse_duration(duration_str) if duration_str else timedelta(seconds=settings["raid_duration_seconds"])
        if not duration:
            await update.message.reply_text("Invalid duration format.")
            return

        expiry_time = datetime.now(timezone.utc) + duration
        msg = f"🚨 **AntiRaid Enabled!** New joins will be temp-banned for the next **{humanize_delta(duration)}**."

    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"manual_antiraid_until": expiry_time}}, upsert=True)
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# ... (Other config commands like /raidtime, /raidactiontime, /autoantiraid would follow a similar pattern, modifying fields in the chat_settings document) ...

# --- The Core Chat Member Handler ---
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main handler that checks every new member."""
    new_member_update = update.chat_member
    if not new_member_update: return

    chat = new_member_update.chat
    new_user = new_member_update.new_chat_member.user
    
    is_join = (new_member_update.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]
               and (not new_member_update.old_chat_member or new_member_update.old_chat_member.status == ChatMemberStatus.LEFT))
    
    if not is_join or new_user.is_bot:
        return
        
    settings = get_raid_settings(chat.id)
    is_raid_active = settings.get("manual_antiraid_until") and settings["manual_antiraid_until"] > datetime.now(timezone.utc)
    
    # --- Auto-Raid Trigger Check ---
    if settings["auto_antiraid_trigger"] > 0 and not is_raid_active:
        now = time.time()
        recent_joins = context.chat_data.setdefault("recent_joins", [])
        recent_joins.append(now)
        recent_joins = [ts for ts in recent_joins if now - ts <= 60]
        context.chat_data["recent_joins"] = recent_joins

        if len(recent_joins) >= settings["auto_antiraid_trigger"]:
            duration = timedelta(seconds=settings["raid_duration_seconds"])
            expiry_time = datetime.now(timezone.utc) + duration
            chat_settings_collection.update_one({"_id": chat.id}, {"$set": {"manual_antiraid_until": expiry_time}}, upsert=True)
            context.chat_data.pop("recent_joins", None)
            
            msg = (f"🚨 **Auto-AntiRaid Triggered!** 🚨\nMore than {settings['auto_antiraid_trigger']} users joined in the last minute. "
                   f"New joins will be temporarily banned for the next **{humanize_delta(duration)}**.")
            await context.bot.send_message(chat.id, msg, parse_mode=ParseMode.HTML)
            is_raid_active = True

    # --- Take Action if AntiRaid is Active ---
    if is_raid_active:
        action_duration = settings["raid_action_duration_seconds"]
        success, action_string = await execute_punishment(context, chat.id, new_user.id, 'tban', action_duration)
        if success:
            log_msg = (f"<b>#ANTIRAID</b>\n"
                       f"<b>User:</b> {new_user.mention_html()} (<code>{new_user.id}</code>)\n"
                       f"<b>Action:</b> Temporarily banned upon joining due to active raid mode.")
            await log_action(context, chat.id, "bans", log_msg)
