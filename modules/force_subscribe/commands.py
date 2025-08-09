from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id

chat_settings_collection = db["chat_settings"]

# --- Helper to check subscription status ---
async def _is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int, channels: list) -> bool:
    """Checks if a user is a member of all required channels."""
    if not channels: return True
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel['id'], user_id=user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                return False
        except BadRequest: return False # Bot not in channel or other issue
        except Exception as e:
            print(f"Error checking subscription for user {user_id} in channel {channel['id']}: {e}")
            return False
    return True

# --- Core Message Handler ---
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main handler that intercepts messages to check for subscription."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat or not update.message: return

    if await is_user_admin(context, chat.id, user.id) or is_user_approved(chat.id, user.id):
        return

    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    if not settings.get("forcesub_enabled", False): return
        
    required_channels = settings.get("forcesub_channels", [])
    if not required_channels: return

    if not await _is_user_subscribed(context, user.id, required_channels):
        try: await update.message.delete()
        except: pass

        channel_links = "\n".join([f"• @{ch['username']}" for ch in required_channels])
        text = (f"Hi {user.mention_html()}, to chat here, you must first join:\n"
                f"{channel_links}\n\n"
                "Please join and then click the button below to verify.")
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ I have joined", callback_data=f"forcesub:verify:{user.id}")
        ]])
        
        warn_msg = await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        context.job_queue.run_once(lambda ctx: ctx.bot.delete_message(chat.id, warn_msg.message_id), 60)

# --- Callback Handler ---
async def verify_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'I have joined' button click."""
    query = update.callback_query
    user_id_to_check = int(query.data.split(":")[2])
    
    if query.from_user.id != user_id_to_check:
        await query.answer("This button is not for you.", show_alert=True)
        return

    settings = chat_settings_collection.find_one({"_id": query.message.chat.id}) or {}
    if await _is_user_subscribed(context, user_id_to_check, settings.get("forcesub_channels", [])):
        await query.answer("Thank you for joining!", show_alert=False)
        try: await query.message.delete()
        except: pass
    else:
        await query.answer("You still haven't joined all required channels.", show_alert=True)

# --- Admin Commands ---
@admin_only
async def forcesub_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds a channel to the force subscribe list."""
    chat_id = await resolve_target_chat_id(update, context)
    channel_username = context.args[0].lstrip('@') if context.args else ""
    if not channel_username:
        await update.message.reply_text("Usage: `/forcesubadd @channelusername`")
        return

    try:
        channel_chat = await context.bot.get_chat(f"@{channel_username}")
        me_member = await channel_chat.get_member(context.bot.id)
        if me_member.status != ChatMemberStatus.ADMINISTRATOR:
            await update.message.reply_text(f"I am not an admin in @{channel_username}. I need to be an admin there to check members.")
            return
    except BadRequest:
        await update.message.reply_text("Could not find that channel, or I am not a member of it.")
        return

    channel_doc = {"id": channel_chat.id, "username": channel_username}
    chat_settings_collection.update_one({"_id": chat_id}, {"$addToSet": {"forcesub_channels": channel_doc}, "$set": {"forcesub_enabled": True}}, upsert=True)
    await update.message.reply_text(f"✅ @{channel_username} is now required to join. Force Subscribe is ON.")

# ... (other admin commands like /forcesubdel, /forcesuboff, /forcesubstatus would be implemented here) ...
