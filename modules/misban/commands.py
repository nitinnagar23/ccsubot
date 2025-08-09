from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, ChatMemberHandler
from telegram.constants import ParseMode, ChatMemberStatus

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id
# Import our granular permission checkers
from utils.permissions import is_user_telegram_admin, is_user_bot_admin, is_user_creator
from utils.moderation import execute_punishment
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- Core Listener ---
async def handle_member_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listens for user removals and checks for betrayal."""
    chat_member_update = update.chat_member
    if not chat_member_update: return

    chat = chat_member_update.chat
    performer = chat_member_update.performer
    
    # We only care about users being KICKED by an admin
    was_member = chat_member_update.old_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]
    is_now_kicked = chat_member_update.new_chat_member.status == ChatMemberStatus.KICKED
    if not (was_member and is_now_kicked and performer): return

    # Check if the feature is enabled
    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    if not settings.get("misban_enabled", False): return

    # --- The Core Betrayal Check ---
    # Safety checks: Don't act on self, or the chat creator
    if performer.id == context.bot.id or await is_user_creator(context, chat.id, performer.id):
        return
        
    # A "rogue" admin is a Telegram admin who is NOT a bot-promoted admin
    is_tg_admin = await is_user_telegram_admin(context, chat.id, performer.id)
    is_bot_admin = is_user_bot_admin(chat.id, performer.id)

    if is_tg_admin and not is_bot_admin:
        # BETRAYAL DETECTED!
        mode = settings.get("misban_mode", "kick")
        success, action_string = await execute_punishment(context, chat.id, performer.id, mode)

        if success and settings.get("misban_notify", True):
            notification_text = (
                f"🚨 <b>Anti-Betrayal System</b> 🚨\n"
                f"{performer.mention_html()} was detected as a rogue admin and has been <b>{action_string}</b>."
            )
            await context.bot.send_message(chat.id, notification_text, parse_mode=ParseMode.HTML)
            
            log_msg = (
                f"<b>#MISBAN</b>\n"
                f"<b>Rogue Admin:</b> {performer.mention_html()} (<code>{performer.id}</code>)\n"
                f"<b>Action:</b> {action_string.capitalize()}"
            )
            await log_action(context, chat.id, "bans", log_msg)


# --- Admin Commands ---
@admin_only
async def toggle_misban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles the Anti-Betrayal system."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["on", "off"]:
        await update.message.reply_text("Usage: `/misban <on/off>`")
        return
        
    enabled = args[0].lower() == "on"
    chat_settings_collection.update_one(
        {"_id": chat_id}, {"$set": {"misban_enabled": enabled}}, upsert=True
    )
    status = "enabled" if enabled else "disabled"
    await update.message.reply_text(f"🛡️ Anti-Betrayal system has been <b>{status}</b>.", parse_mode=ParseMode.HTML)

# ... (Implement /misbannotify, /misbanmode, /misbanconfig following the same pattern) ...
