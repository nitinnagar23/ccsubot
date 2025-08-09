from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.context import resolve_target_chat_id
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options

chat_settings_collection = db["chat_settings"]
DEFAULT_RULES_TEXT = "No rules have been set for this chat yet."

# --- User Command ---
@check_disabled
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the chat rules."""
    # Check if this was triggered by a deep link from another chat
    target_chat_id = context.user_data.get('deep_link_chat_id') or await resolve_target_chat_id(update, context)
    
    settings = chat_settings_collection.find_one({"_id": target_chat_id}) or {}
    raw_text = settings.get("rules_text", DEFAULT_RULES_TEXT)

    # Handle 'noformat' keyword
    if context.args and context.args[0].lower() == 'noformat':
        await update.message.reply_text(f"```\n{raw_text}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        return

    # Check privacy setting
    if settings.get("private_rules", False) and update.effective_chat.type != 'private':
        pm_keyboard = [[InlineKeyboardButton("📖 Click here to view the rules", url=f"https://t.me/{context.bot.username}?start=rules_{target_chat_id}")]]
        await update.message.reply_text("The rules for this chat will be sent to you in a private message.", reply_markup=InlineKeyboardMarkup(pm_keyboard))
        return

    # Use the Full Formatting Pipeline
    chosen_text = select_random(raw_text)
    send_options = extract_send_options(chosen_text)
    filled_text = apply_fillings(chosen_text, update)
    final_text, keyboard = parse_buttons(filled_text)

    await update.message.reply_text(final_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2, **send_options)

# --- Admin Commands ---
@admin_only
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the rules for the chat."""
    chat_id = await resolve_target_chat_id(update, context)
    rules_text = update.message.text.split(" ", 1)[1] if len(context.args) > 0 else ""
    if not rules_text:
        await update.message.reply_text("You need to provide the rules text after the command.")
        return
        
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"rules_text": rules_text}}, upsert=True)
    await update.message.reply_text("✅ The rules for this chat have been updated.")

# ... (Implement /resetrules, /privaterules, /setrulesbutton following simple DB update patterns) ...
