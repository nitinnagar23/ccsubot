from telegram import Update
from telegram.ext import ContextTypes

from database.db import db

chat_settings_collection = db["chat_settings"]

async def resolve_target_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Determines the target chat for an action.
    If the user is connected to another chat via /connect, it returns the connected chat's ID.
    Otherwise, it returns the ID of the chat where the command was sent.
    """
    # user_data is a dictionary attached to each user, perfect for this.
    if 'connected_chat_id' in context.user_data:
        return context.user_data['connected_chat_id']
    else:
        return update.effective_chat.id

async def resolve_action_topic_id(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> int | None:
    """
    For forum chats, determines the designated topic for bot actions.
    If an action topic is set, returns its ID. Otherwise, returns None.
    """
    try:
        chat = await context.bot.get_chat(chat_id)
        if not chat.is_forum:
            return None
    except Exception:
        # Chat might not be found if the bot was kicked
        return None

    settings = chat_settings_collection.find_one({"_id": chat_id}, {"action_topic_id": 1})
    return settings.get("action_topic_id") if settings else None
