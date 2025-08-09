import time
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id
from utils.moderation import execute_punishment

locks_collection = db["locks"]
chat_settings_collection = db["chat_settings"]

# --- Constants for Validation and Help Text ---
LOCK_TYPES = {
    "sticker": "Stickers", "photo": "Photos", "video": "Videos", "animation": "GIFs/Animations",
    "document": "Documents/Files", "url": "Links/URLs", "forward": "Forwarded messages",
    "invitelink": "Telegram invite links (t.me/+)", "command": "Bot commands", "contact": "Contacts",
    "poll": "Polls", "voice": "Voice messages", "audio": "Audio files", "videonote": "Video Notes (Telescopes)",
}

# --- Core Listener ---
async def check_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The MessageHandler that checks every message against the active locks."""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not chat or not user or not message or user.is_bot: return

    if await is_user_admin(context, chat.id, user.id) or is_user_approved(chat.id, user.id):
        return

    # --- Caching Logic ---
    now = time.time()
    cached_data = context.chat_data.get('cached_locks')
    if cached_data and now - cached_data.get('timestamp', 0) < 60:
        active_locks = cached_data['locks']
    else:
        active_locks = {lock['lock_type']: lock for lock in locks_collection.find({"chat_id": chat.id})}
        context.chat_data['cached_locks'] = {'timestamp': now, 'locks': active_locks}
    
    if not active_locks: return

    # --- Check message content against active locks ---
    triggered_lock_type = None
    if message.sticker and 'sticker' in active_locks: triggered_lock_type = 'sticker'
    elif message.photo and 'photo' in active_locks: triggered_lock_type = 'photo'
    # ... add all other message types from LOCK_TYPES constant ...
    elif message.forward_date and 'forward' in active_locks: triggered_lock_type = 'forward'
    elif (message.entities or message.caption_entities):
        for entity in (message.entities or message.caption_entities):
            if entity.type == 'url' and 'url' in active_locks:
                triggered_lock_type = 'url'
                break
    
    if triggered_lock_type:
        lock_rule = active_locks[triggered_lock_type]
        action = lock_rule.get('action', 'del') # Default action is always delete
        duration_sec = lock_rule.get('action_duration_seconds', 0)

        # In a full implementation, you would check the allowlist here before proceeding.
        
        try:
            if action == 'del':
                await message.delete()
            else:
                # Use our centralized punishment utility for other actions
                await message.delete() # Always delete the offending message
                await execute_punishment(context, chat.id, user.id, action, duration_sec)

            settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
            if settings.get("lock_warns_enabled", False):
                warn_msg = await context.bot.send_message(
                    chat.id,
                    f"{user.mention_html()}, your message was removed because **{LOCK_TYPES.get(triggered_lock_type, 'locked content')}** is not allowed here.",
                    parse_mode=ParseMode.HTML
                )
                context.job_queue.run_once(
                    lambda ctx: ctx.bot.delete_message(chat.id, warn_msg.message_id),
                    15
                )
        except Exception as e:
            print(f"Failed to execute lock action: {e}")

# --- Admin Commands ---
@admin_only
async def lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Locks one or more message types."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args:
        await update.message.reply_text("You need to specify what to lock. See /locktypes.")
        return

    types_to_lock = [arg.lower() for arg in args if arg.lower() in LOCK_TYPES]
    
    for lock_type in types_to_lock:
        locks_collection.update_one(
            {"chat_id": chat_id, "lock_type": lock_type},
            {"$set": {"action": "del"}}, # Set a default action
            upsert=True
        )
    
    await update.message.reply_text(f"✅ Locked: `{'`, `'.join(types_to_lock)}`.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unlocks one or more message types."""
    chat_id = await resolve_target_chat_id(update, context)
    types_to_unlock = [arg.lower() for arg in context.args]
    if not types_to_unlock:
        await update.message.reply_text("You need to specify what to unlock.")
        return
        
    locks_collection.delete_many({"chat_id": chat_id, "lock_type": {"$in": types_to_unlock}})
    await update.message.reply_text(f"✅ Unlocked: `{'`, `'.join(types_to_unlock)}`.", parse_mode=ParseMode.MARKDOWN_V2)

@admin_only
async def list_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all currently active locks."""
    chat_id = await resolve_target_chat_id(update, context)
    active_locks = list(locks_collection.find({"chat_id": chat_id}))
    if not active_locks:
        await update.message.reply_text("No items are currently locked.")
        return
        
    msg = "<b>The following items are locked:</b>\n"
    msg += "\n".join([f"• <code>{lock['lock_type']}</code>" for lock in active_locks])
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
