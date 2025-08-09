from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id, resolve_action_topic_id
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]
DEFAULT_WELCOME = "Hello {first}, welcome to {chatname}!"
DEFAULT_GOODBYE = "Goodbye, {first}!"

# --- Job for cleaning welcome messages ---
async def _delete_welcome_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to delete the welcome message after a timeout."""
    job_data = context.job.data
    try:
        await context.bot.delete_message(chat_id=job_data['chat_id'], message_id=job_data['message_id'])
    except BadRequest: pass

# --- Core Chat Member Handler ---
async def handle_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user join and leave events to send greetings."""
    member_update = update.chat_member
    if not member_update: return

    chat = member_update.chat
    user = member_update.new_chat_member.user
    old_status = member_update.old_chat_member.status
    new_status = member_update.new_chat_member.status
    
    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    action_topic_id = await resolve_action_topic_id(context, chat.id)

    # --- Handle User Joins (Welcome) ---
    is_join = new_status == ChatMemberStatus.MEMBER and old_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
    if is_join:
        # IMPORTANT: If CAPTCHA is enabled, it handles the welcome message. This prevents double messages.
        if settings.get("captcha_enabled", False):
            return

        if settings.get("welcome_enabled", False):
            if settings.get("clean_welcome_enabled", False):
                last_welcome_id = context.chat_data.pop('last_welcome_message_id', None)
                if last_welcome_id:
                    try: await context.bot.delete_message(chat.id, last_welcome_id)
                    except: pass
            
            raw_text = settings.get("welcome_message", DEFAULT_WELCOME)
            
            chosen_text = select_random(raw_text)
            send_options = extract_send_options(chosen_text)
            filled_text = apply_fillings(chosen_text, update)
            final_text, keyboard = parse_buttons(filled_text)
            
            sent_message = await context.bot.send_message(
                chat.id, text=final_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2,
                message_thread_id=action_topic_id, **send_options
            )
            
            if settings.get("clean_welcome_enabled", False):
                context.chat_data['last_welcome_message_id'] = sent_message.message_id
                context.job_queue.run_once(
                    _delete_welcome_job, 300, # 5 minutes
                    data={'chat_id': chat.id, 'message_id': sent_message.message_id},
                    name=f"del_welcome_{chat.id}_{sent_message.message_id}"
                )
        
        log_msg = f"<b>#JOIN</b>\n<b>User:</b> {user.mention_html()} (<code>{user.id}</code>)"
        await log_action(context, chat.id, "joins", log_msg)

    # --- Handle User Leaves (Goodbye) ---
    is_leave = new_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED] and old_status == ChatMemberStatus.MEMBER
    if is_leave:
        if settings.get("goodbye_enabled", False):
            raw_text = settings.get("goodbye_message", DEFAULT_GOODBYE)
            chosen_text = select_random(raw_text)
            send_options = extract_send_options(chosen_text)
            filled_text = apply_fillings(chosen_text, update)
            final_text, keyboard = parse_buttons(filled_text)
            
            await context.bot.send_message(
                chat.id, text=final_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2,
                message_thread_id=action_topic_id, **send_options
            )
        
        log_msg = f"<b>#LEAVE</b>\n<b>User:</b> {user.mention_html()} (<code>{user.id}</code>)"
        await log_action(context, chat.id, "leaves", log_msg)


# --- Admin Commands ---
@admin_only
async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable or disable welcome messages."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["on", "off", "yes", "no"]:
        await update.message.reply_text("Usage: `/welcome <on/off>`")
        return
        
    enabled = args[0].lower() in ["on", "yes"]
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"welcome_enabled": enabled}}, upsert=True)
    status = "enabled" if enabled else "disabled"
    await update.message.reply_text(f"✅ Welcome messages have been **{status}**.", parse_mode=ParseMode.HTML)

@admin_only
async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the welcome message."""
    chat_id = await resolve_target_chat_id(update, context)
    welcome_text = update.message.text.split(" ", 1)[1] if len(context.args) > 0 else ""
    if not welcome_text:
        await update.message.reply_text("You need to provide a message to set! For example:\n`/setwelcome Hello {first}!`")
        return
    
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"welcome_message": welcome_text}}, upsert=True)
    await update.message.reply_text("✅ New welcome message has been saved. Here is a preview:")
    
    # Send a preview using the formatter
    final_text, keyboard = parse_buttons(apply_fillings(welcome_text, update))
    await update.message.reply_text(final_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2)

# ... (Implement /resetwelcome, /goodbye, /setgoodbye, /resetgoodbye, /cleanwelcome following the same patterns) ...
