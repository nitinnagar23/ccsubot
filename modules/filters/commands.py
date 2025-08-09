import re
import time
import random
from telegram import Update, Message, BotCommand
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

# --- Local Imports ---
from database.db import db
from utils.decorators import admin_only
from utils.permissions import is_user_admin, is_user_approved
from utils.context import resolve_target_chat_id
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options

# --- Service Integrations ---
from modules.cleaning_bot_messages.service import schedule_bot_message_deletion
from modules.log_channels.service import log_action

filters_collection = db["filters"]
chat_settings_collection = db["chat_settings"]

# --- Helper Functions ---
async def _update_chat_commands(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Fetches all command-filters for a chat and updates the / menu for admins."""
    command_filters = list(filters_collection.find({"chat_id": chat_id, "is_command": True}))
    
    bot_commands = [
        BotCommand(f.get("trigger", "").lstrip('/!'), f.get("command_description", "Custom command"))
        for f in command_filters
    ]
    
    try:
        await context.bot.set_my_commands(bot_commands, scope={'type': 'chat_administrators', 'chat_id': chat_id})
    except Exception as e:
        print(f"Could not set commands for chat {chat_id}: {e}")

# --- Admin Commands ---
@admin_only
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds or updates a filter."""
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    
    trigger_str = args[0] if args else ""
    reply_text = " ".join(args[1:])
    
    file_id, file_type = None, None
    if update.message.reply_to_message:
        reply_msg = update.message.reply_to_message
        if not reply_text: reply_text = reply_msg.caption or ""
        
        if reply_msg.photo: file_id, file_type = reply_msg.photo[-1].file_id, 'photo'
        elif reply_msg.document: file_id, file_type = reply_msg.document.file_id, 'document'
        elif reply_msg.video: file_id, file_type = reply_msg.video.file_id, 'video'
        elif reply_msg.sticker: file_id, file_type = reply_msg.sticker.file_id, 'sticker'
        elif reply_msg.animation: file_id, file_type = reply_msg.animation.file_id, 'animation'

    if not trigger_str:
        await update.message.reply_text("You need to specify a trigger for the filter.")
        return

    permission = "admin" if "{admin}" in reply_text else "user" if "{user}" in reply_text else "all"
    is_command = "{command}" in reply_text
    command_desc_match = re.search(r"\{command\s+(.+?)\}", reply_text)
    command_description = command_desc_match.group(1) if command_desc_match else trigger_str
    clean_reply = re.sub(r"\{[^}]+\}", "", reply_text).strip()
    match_type = 'exact' if trigger_str.lower().startswith('exact:') else 'prefix' if trigger_str.lower().startswith('prefix:') else 'contains'
    trigger_str = trigger_str[6:] if match_type == 'exact' else trigger_str[7:] if match_type == 'prefix' else trigger_str
    
    filters_collection.update_one(
        {"chat_id": chat_id, "trigger": trigger_str},
        {"$set": {"reply": clean_reply, "file_id": file_id, "file_type": file_type, "permission": permission, "match_type": match_type, "is_command": is_command, "command_description": command_description}}, 
        upsert=True
    )
    await update.message.reply_text(f"✅ Filter for `{trigger_str}` has been saved.", parse_mode=ParseMode.MARKDOWN_V2)
    if is_command: await _update_chat_commands(context, chat_id)

@admin_only
async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Removes a filter."""
    chat_id = await resolve_target_chat_id(update, context)
    trigger_to_stop = " ".join(context.args)
    if not trigger_to_stop: return
        
    result = filters_collection.find_one_and_delete({"chat_id": chat_id, "trigger": trigger_to_stop})
    if result:
        await update.message.reply_text(f"✅ Filter for `{trigger_to_stop}` has been stopped.", parse_mode=ParseMode.MARKDOWN_V2)
        if result.get("is_command"): await _update_chat_commands(context, chat_id)
    else:
        await update.message.reply_text("That filter doesn't exist.")

@admin_only
async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all active filters in the chat."""
    chat_id = await resolve_target_chat_id(update, context)
    all_filters = list(filters_collection.find({"chat_id": chat_id}))
    if not all_filters:
        await update.message.reply_text("There are no filters in this chat.")
        return
        
    msg = "<b>Active filters in this chat:</b>\n"
    msg += "\n".join([f"- <code>{f['trigger']}</code>" for f in all_filters])
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# --- The Core Message Handler ---
async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The main handler that checks every message for a filter match."""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not user or user.is_bot: return

    if await is_user_admin(context, chat.id, user.id) or is_user_approved(chat.id, user.id): return

    now = time.time()
    cached_data = context.chat_data.get('cached_filters')
    if cached_data and now - cached_data.get('timestamp', 0) < 60:
        all_filters = cached_data['filters']
    else:
        all_filters = list(filters_collection.find({"chat_id": chat.id}))
        context.chat_data['cached_filters'] = {'timestamp': now, 'filters': all_filters}
    
    if not all_filters: return

    text = (message.text or message.caption or "").lower()
    
    for f in all_filters:
        trigger = f.get("trigger", "").lower()
        if (f.get("permission") == "admin" and not await is_user_admin(context, chat.id, user.id)): continue
        
        is_match = (f.get("match_type") == "contains" and trigger in text) or \
                   (f.get("match_type") == "exact" and trigger == text) or \
                   (f.get("match_type") == "prefix" and text.startswith(trigger))
        
        if is_match:
            raw_reply = f.get("reply", "")
            chosen_reply = select_random(raw_reply)
            send_options = extract_send_options(chosen_reply)
            filled_reply = apply_fillings(chosen_reply, update)
            final_text, keyboard = parse_buttons(filled_reply)

            sent_message = None
            try:
                if f.get("file_id"):
                    file_type = f.get("file_type")
                    sender_func = getattr(message, f"reply_{file_type}", None)
                    if sender_func:
                        sent_message = await sender_func(f.get("file_id"), caption=final_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, **send_options)
                else:
                    sent_message = await message.reply_text(final_text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True, **send_options)
                
                # --- INTEGRATION ---
                if sent_message:
                    schedule_bot_message_deletion(context, sent_message, "filter")
            except Exception as e:
                print(f"Failed to send filter reply: {e}")

            return
