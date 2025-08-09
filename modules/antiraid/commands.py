import time
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus

# --- Local Imports ---
from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id
from utils.time import parse_duration, humanize_delta
from utils.moderation import execute_punishment

# --- Service Integrations ---
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
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    settings = get_raid_settings(chat_id)
    
    log_value = ""
    if args and args[0].lower() in ["off", "no"]:
        expiry_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        msg = "✅ AntiRaid has been manually disabled."
        log_value = "Disabled"
    else:
        duration_str = args[0] if args else None
        duration = parse_duration(duration_str) if duration_str else timedelta(seconds=settings["raid_duration_seconds"])
        if not duration:
            await update.message.reply_text("Invalid duration format.")
            return

        expiry_time = datetime.now(timezone.utc) + duration
        human_duration = humanize_delta(duration)
        msg = f"🚨 <b>AntiRaid Enabled!</b>\nNew joins will be temporarily banned for the next <b>{human_duration}</b>."
        log_value = f"Enabled for {human_duration}"

    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"manual_antiraid_until": expiry_time}}, upsert=True)
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> AntiRaid\n<b>New Value:</b> {log_value}")
    await log_action(context, chat_id, "settings", log_msg)


@admin_only
async def raid_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Views or sets the default duration for manual antiraid."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    
    if not args:
        settings = get_raid_settings(chat_id)
        duration = timedelta(seconds=settings["raid_duration_seconds"])
        await update.message.reply_text(f"The current default antiraid duration is <b>{humanize_delta(duration)}</b>.", parse_mode=ParseMode.HTML)
        return

    duration = parse_duration(args[0])
    if not duration or duration.total_seconds() <= 0:
        await update.message.reply_text("Invalid duration format.")
        return

    chat_settings_collection.update_one(
        {"_id": chat_id}, {"$set": {"raid_duration_seconds": duration.total_seconds()}}, upsert=True)
    
    human_duration = humanize_delta(duration)
    await update.message.reply_text(f"Default antiraid duration has been set to <b>{human_duration}</b>.", parse_mode=ParseMode.HTML)
    
    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> Default Raid Duration\n<b>New Value:</b> {human_duration}")
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def raid_action_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Views or sets the duration for the temporary ban."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args

    if not args:
        settings = get_raid_settings(chat_id)
        duration = timedelta(seconds=settings["raid_action_duration_seconds"])
        await update.message.reply_text(f"Users joining during a raid will be temp-banned for <b>{humanize_delta(duration)}</b>.", parse_mode=ParseMode.HTML)
        return

    duration = parse_duration(args[0])
    if not duration or duration.total_seconds() <= 0:
        await update.message.reply_text("Invalid duration format.")
        return

    chat_settings_collection.update_one(
        {"_id": chat_id}, {"$set": {"raid_action_duration_seconds": duration.total_seconds()}}, upsert=True)
    
    human_duration = humanize_delta(duration)
    await update.message.reply_text(f"Antiraid temp-ban duration set to <b>{human_duration}</b>.", parse_mode=ParseMode.HTML)
    
    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> Raid Action Duration\n<b>New Value:</b> {human_duration}")
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def auto_antiraid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the trigger for automatic antiraid."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/autoantiraid <number of joins/off>`")
        return

    arg = args[0].lower()
    log_value = ""
    if arg in ["off", "no", "0"]:
        trigger, msg, log_value = 0, "✅ Automatic antiraid has been disabled.", "Disabled"
    elif arg.isdigit() and int(arg) >= 2:
        trigger, msg, log_value = int(arg), f"Automatic antiraid will now trigger if <b>{arg}</b> or more users join within a minute.", arg
    else:
        await update.message.reply_text("Invalid input. Please use a number (>=2) or 'off'.")
        return

    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"auto_antiraid_trigger": trigger}}, upsert=True)
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    log_msg = (f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n"
               f"<b>Setting:</b> Auto AntiRaid Trigger\n<b>New Value:</b> {log_value}")
    await log_action(context, chat_id, "settings", log_msg)

# --- The Core Chat Member Handler ---
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main handler that checks every new member."""
    # ... (This function is already complete from the previous response, no changes needed) ...
    new_member_update = update.chat_member
    if not new_member_update: return
    chat = new_member_update.chat
    new_user = new_member_update.new_chat_member.user
    is_join = (new_member_update.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]
               and (not new_member_update.old_chat_member or new_member_update.old_chat_member.status == ChatMemberStatus.LEFT))
    if not is_join or new_user.is_bot: return
    settings = get_raid_settings(chat.id)
    is_raid_active = settings.get("manual_antiraid_until") and settings["manual_antiraid_until"] > datetime.now(timezone.utc)
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
            human_duration = humanize_delta(duration)
            msg = (f"🚨 <b>Auto-AntiRaid Triggered!</b> 🚨\nMore than {settings['auto_antiraid_trigger']} users joined in the last minute. "
                   f"New joins will be temporarily banned for the next <b>{human_duration}</b>.")
            await context.bot.send_message(chat.id, msg, parse_mode=ParseMode.HTML)
            log_msg = (f"<b>#ANTIRAID_AUTO</b>\n"
                       f"<b>Trigger:</b> {settings['auto_antiraid_trigger']} joins/min\n"
                       f"<b>Action:</b> Enabled for {human_duration}")
            await log_action(context, chat.id, "settings", log_msg)
            is_raid_active = True
    if is_raid_active:
        action_duration = settings["raid_action_duration_seconds"]
        success, action_string = await execute_punishment(context, chat.id, new_user.id, 'tban', action_duration)
        if success:
            log_msg = (f"<b>#ANTIRAID</b>\n"
                       f"<b>User:</b> {new_user.mention_html()} (<code>{new_user.id}</code>)\n"
                       f"<b>Action:</b> {action_string.capitalize()} on join.")
            await log_action(context, chat.id, "bans", log_msg)
