from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.context import resolve_target_chat_id
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- User Commands ---
@check_disabled
async def get_pinned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the currently pinned message to the chat."""
    target_chat_id = await resolve_target_chat_id(update, context)
    
    try:
        chat_obj = await context.bot.get_chat(target_chat_id)
        pinned_msg = chat_obj.pinned_message
        
        if not pinned_msg:
            await update.message.reply_text("There is no pinned message in this chat.")
            return
            
        # Forwarding is a clean way to resend any type of content.
        # We forward it to the chat where the command was issued.
        await pinned_msg.forward(update.effective_chat.id)
        
    except BadRequest as e:
        await update.message.reply_text(f"Could not retrieve pinned message: {e.message}")

# --- Admin Commands ---
@admin_only
async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pins the message replied to."""
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a message to pin it.")
        return
        
    disable_notification = not (context.args and context.args[0].lower() in ['loud', 'notify'])
    
    try:
        await update.message.reply_to_message.pin(disable_notification=disable_notification)
        # Log this action
        admin = update.effective_user
        chat = update.effective_chat
        log_msg = (f"<b>#PIN</b>\n"
                   f"<b>Admin:</b> {admin.mention_html()}\n"
                   f"Pinned a <a href='{update.message.reply_to_message.link}'>message</a>.")
        await log_action(context, chat.id, "settings", log_msg)
    except BadRequest as e:
        await update.message.reply_text(f"Could not pin message: {e.message}")

@admin_only
async def perma_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a new message with formatting and pins it."""
    target_chat_id = await resolve_target_chat_id(update, context)
    raw_text = update.message.text.split(" ", 1)[1] if len(context.args) > 0 else ""

    if not raw_text:
        await update.message.reply_text("You need to provide text for the permapin!")
        return
        
    # Use the full formatting pipeline
    chosen_text = select_random(raw_text)
    send_options = extract_send_options(chosen_text)
    filled_text = apply_fillings(chosen_text, update)
    final_text, keyboard = parse_buttons(filled_text)
    
    try:
        sent_message = await context.bot.send_message(
            target_chat_id, text=final_text, reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2, **send_options
        )
        await sent_message.pin(disable_notification=True)
    except BadRequest as e:
        await update.message.reply_text(f"Could not create permapin: {e.message}")

@admin_only
async def unpin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unpins a message."""
    target_chat_id = await resolve_target_chat_id(update, context)
    try:
        if update.message.reply_to_message:
            await context.bot.unpin_chat_message(target_chat_id, update.message.reply_to_message.message_id)
            await update.message.reply_text("That specific message has been unpinned.")
        else:
            await context.bot.unpin_chat_message(target_chat_id)
            await update.message.reply_text("The latest pinned message has been unpinned.")
    except BadRequest as e:
        await update.message.reply_text(f"Could not unpin message: {e.message}")

# ... (Implement /unpinall, /antichannelpin, and /cleanlinked following similar patterns) ...

# --- Listeners for Automated Features ---
async def handle_auto_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listener to automatically unpin messages from a linked channel."""
    message = update.effective_message
    chat = update.effective_chat
    
    settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
    if not settings.get("antichannelpin_enabled", False): return
        
    pinned_msg = message.pinned_message
    if pinned_msg and pinned_msg.sender_chat and chat.linked_chat_id and pinned_msg.sender_chat.id == chat.linked_chat_id:
        try:
            await context.bot.unpin_chat_message(chat.id)
        except BadRequest: pass
