import re
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import MessageHandler, ChatMemberHandler, filters, ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus

from utils.permissions import is_user_admin, is_user_approved
from database.db import db

chat_settings_collection = db["chat_settings"]
group_members_collection = db["group_members"]

async def track_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ChatMemberHandler to record when a new user joins."""
    new_member_update = update.chat_member
    if not new_member_update: return

    is_join = (new_member_update.new_chat_member.status == ChatMemberStatus.MEMBER 
               and new_member_update.old_chat_member.status == ChatMemberStatus.LEFT)
    if not is_join: return

    chat_id = new_member_update.chat.id
    user_id = new_member_update.new_chat_member.user.id
    
    group_members_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"join_timestamp": datetime.now(timezone.utc)}},
        upsert=True
    )

async def check_for_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main handler that checks messages from non-admins."""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not chat or not user or user.is_bot: return
        
    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    if not settings.get("spam_guard_enabled", False): return
        
    if await is_user_admin(context, chat.id, user.id) or is_user_approved(chat.id, user.id):
        return

    # --- New User Quarantine Check ---
    quarantine_seconds = settings.get("quarantine_seconds", 86400) # Default to 24 hours
    if quarantine_seconds > 0:
        member_data = group_members_collection.find_one({"chat_id": chat.id, "user_id": user.id})
        if member_data and member_data.get("join_timestamp"):
            if datetime.now(timezone.utc) - member_data["join_timestamp"] < timedelta(seconds=quarantine_seconds):
                is_violating = (
                    message.forward_date or 
                    any(e.type in ['url', 'text_link'] for e in (message.entities or [])) or
                    message.photo or message.video or message.document or message.sticker or message.animation
                )
                if is_violating:
                    try:
                        await message.delete()
                        warn_msg = await update.message.reply_text(
                            f"{user.mention_html()}, new members are not permitted to send links, media, or forwards for a short period.",
                            parse_mode=ParseMode.HTML
                        )
                        context.job_queue.run_once(lambda ctx: ctx.bot.delete_message(chat.id, warn_msg.message_id), 20)
                    except: pass
                    return
