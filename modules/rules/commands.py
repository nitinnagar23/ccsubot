from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# --- Local Imports ---
from database.db import db
from utils.decorators import admin_only, check_disabled
from utils.context import resolve_target_chat_id
from utils.formatters import select_random, apply_fillings, parse_buttons, extract_send_options, escape_markdown_v2

# --- Service Integrations ---
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]
DEFAULT_RULES_TEXT = "No rules have been set for this chat yet."

# --- User Command ---
@check_disabled
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the chat rules, with proper escaping."""
    target_chat_id = context.user_data.get('deep_link_chat_id') or await resolve_target_chat_id(update, context)
    
    settings = chat_settings_collection.find_one({"_id": target_chat_id}) or {}
    raw_text = settings.get("rules_text", DEFAULT_RULES_TEXT)

    if context.args and context.args[0].lower() == 'noformat':
        await update.message.reply_text(f"```\n{raw_text}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        return

    if settings.get("private_rules", False) and update.effective_chat.type != 'private':
        pm_keyboard = [[InlineKeyboardButton("📖 Click here to view the rules", url=f"https://t.me/{context.bot.username}?start=rules_{target_chat_id}")]]
        await update.message.reply_text("The rules for this chat will be sent to you in a private message.", reply_markup=InlineKeyboardMarkup(pm_keyboard))
        return

    # Corrected Formatting Pipeline
    chosen_text = select_random(raw_text)
    send_options = extract_send_options(chosen_text)
    filled_text = apply_fillings(chosen_text, update)
    text_before_escaping, keyboard = parse_buttons(filled_text)
    final_text = escape_markdown_v2(text_before_escaping)
    
    await update.message.reply_text(
        final_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2, **send_options)

# --- Admin Commands ---
@admin_only
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the rules for the chat."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    rules_text = update.message.text.split(" ", 1)[1] if len(context.args) > 0 else ""
    
    if not rules_text:
        await update.message.reply_text("You need to provide the rules text after the command.")
        return
        
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"rules_text": rules_text}}, upsert=True)
    await update.message.reply_text("✅ The rules for this chat have been updated.")
    
    log_msg = f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n<b>Setting:</b> Rules\nUpdated the chat rules."
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def reset_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resets the chat rules to default."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    
    chat_settings_collection.update_one({"_id": chat_id}, {"$unset": {"rules_text": ""}}, upsert=True)
    await update.message.reply_text("✅ The rules for this chat have been reset.")

    log_msg = f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n<b>Setting:</b> Rules\nReset the chat rules to default."
    await log_action(context, chat_id, "settings", log_msg)
    
@admin_only
async def toggle_private_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle whether rules are sent in PM."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    args = context.args
    if not args or args[0].lower() not in ["on", "off", "yes", "no"]:
        await update.message.reply_text("Usage: `/privaterules <on/off>`")
        return
        
    enabled = args[0].lower() in ["on", "yes"]
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"private_rules": enabled}}, upsert=True)
    status = "will now be sent in private" if enabled else "will now be sent in the group"
    await update.message.reply_text(f"✅ Rules {status}.")

    log_msg = f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n<b>Setting:</b> Private Rules\n<b>New Value:</b> {'Enabled' if enabled else 'Disabled'}"
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def set_rules_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the text for the {rules} button."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    button_text = " ".join(context.args)
    if not button_text:
        await update.message.reply_text("Usage: `/setrulesbutton <button text>`")
        return
        
    chat_settings_collection.update_one({"_id": chat_id}, {"$set": {"rules_button_text": button_text}}, upsert=True)
    await update.message.reply_text(f"✅ The `{{rules}}` button will now say: \"{button_text}\"", parse_mode=ParseMode.MARKDOWN_V2)

    log_msg = f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n<b>Setting:</b> Rules Button Text\n<b>New Value:</b> {button_text}"
    await log_action(context, chat_id, "settings", log_msg)

@admin_only
async def reset_rules_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resets the {rules} button text to default."""
    admin = update.effective_user
    chat_id = await resolve_target_chat_id(update, context)
    
    chat_settings_collection.update_one({"_id": chat_id}, {"$unset": {"rules_button_text": ""}}, upsert=True)
    await update.message.reply_text("✅ The {rules} button text has been reset to default.")

    log_msg = f"<b>#SETTINGS_CHANGE</b>\n<b>Admin:</b> {admin.mention_html()}\n<b>Setting:</b> Rules Button Text\nReset to default."
    await log_action(context, chat_id, "settings", log_msg)
