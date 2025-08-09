from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from database.db import db
from utils.decorators import admin_only
from utils.context import resolve_target_chat_id
from modules.log_channels.service import log_action

chat_settings_collection = db["chat_settings"]

# --- Helper to check for Forum and get topic ID ---
async def _get_topic_id_if_forum(update: Update) -> int | None:
    """Checks if chat is a forum. Returns current topic ID or None if not a forum."""
    chat = update.effective_chat
    if not chat.is_forum:
        await update.message.reply_text("This command only works in chats with Topics enabled.")
        return None
    # message_thread_id is None for the 'General' topic, which is a valid topic.
    return update.message.message_thread_id

# --- Admin Commands ---
@admin_only
async def set_action_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the current topic as the default for bot actions."""
    chat_id = await resolve_target_chat_id(update, context)
    topic_id = await _get_topic_id_if_forum(update)
    if topic_id is None and not update.effective_chat.is_forum: return

    chat_settings_collection.update_one(
        {"_id": chat_id}, {"$set": {"action_topic_id": topic_id}}, upsert=True
    )
    topic_name = update.message.reply_to_message.forum_topic_created.name if update.message.message_thread_id else "General"
    await update.message.reply_text(f"✅ The '{topic_name}' topic is now the default for automated messages.")

@admin_only
async def get_action_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gets the currently configured action topic."""
    chat_id = await resolve_target_chat_id(update, context)
    if not update.effective_chat.is_forum:
        await update.message.reply_text("This chat does not have Topics enabled.")
        return
        
    settings = chat_settings_collection.find_one({"_id": chat_id}) or {}
    topic_id = settings.get("action_topic_id")
    
    if topic_id:
        # Getting the topic name from ID is not straightforward, so we just show the ID.
        await update.message.reply_text(f"The current action topic ID is: <code>{topic_id}</code>.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("No action topic is set. Messages will be sent in the 'General' topic or where the event occurs.")

@admin_only
async def new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Creates a new topic."""
    chat_id = await resolve_target_chat_id(update, context)
    if await _get_topic_id_if_forum(update) is None and not update.effective_chat.is_forum: return
        
    topic_name = " ".join(context.args)
    if not topic_name:
        await update.message.reply_text("Usage: `/newtopic <name>`")
        return
        
    try:
        await context.bot.create_forum_topic(chat_id, name=topic_name)
        await log_action(context, chat_id, "settings", f"<b>#TOPIC_CREATED</b>\n<b>Admin:</b> {update.effective_user.mention_html()}\n<b>Name:</b> {topic_name}")
    except BadRequest as e:
        await update.message.reply_text(f"Could not create topic: {e.message}")

@admin_only
async def rename_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Renames the current topic."""
    chat_id = await resolve_target_chat_id(update, context)
    topic_id = await _get_topic_id_if_forum(update)
    if topic_id is None: return
        
    new_name = " ".join(context.args)
    if not new_name:
        await update.message.reply_text("Usage: `/renametopic <new name>`")
        return
        
    try:
        await context.bot.edit_forum_topic(chat_id, message_thread_id=topic_id, name=new_name)
        await update.message.reply_text("✅ Topic renamed.")
    except BadRequest as e:
        await update.message.reply_text(f"Could not rename topic: {e.message}")

@admin_only
async def close_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Closes the current topic."""
    chat_id = await resolve_target_chat_id(update, context)
    topic_id = await _get_topic_id_if_forum(update)
    if topic_id is None: return
    try:
        await context.bot.edit_forum_topic(chat_id, message_thread_id=topic_id, is_closed=True)
        await update.message.reply_text("✅ Topic closed.")
    except BadRequest as e:
        await update.message.reply_text(f"Could not close topic: {e.message}")

# ... (Implement /reopentopic and /deletetopic following the same patterns) ...
