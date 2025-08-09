from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

from database.db import db # <-- CORRECT: Import the main db object
from .config import BOT_OWNERS

# CORRECT: Get the collection from the db object
chat_settings_collection = db["chat_settings"]

# --- Granular Permission Checkers ---
async def is_user_creator(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """Checks if a user is the creator of the chat."""
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        for admin in chat_admins:
            if admin.status == ChatMemberStatus.CREATOR and admin.user.id == user_id:
                return True
        return False
    except Exception:
        return False

async def is_user_telegram_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """Checks if a user is a native Telegram admin (creator or administrator)."""
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        return user_id in {admin.user.id for admin in chat_admins}
    except Exception:
        return False

def is_user_bot_admin(chat_id: int, user_id: int) -> bool:
    """Checks if a user was promoted via the bot's /promote command."""
    settings = chat_settings_collection.find_one({"_id": chat_id}, {"promoted_users": 1})
    return bool(settings and user_id in settings.get("promoted_users", []))

def is_user_owner(user_id: int) -> bool:
    """Checks if a user is one of the bot owners."""
    return user_id in BOT_OWNERS

def is_user_approved(chat_id: int, user_id: int) -> bool:
    """Checks if a user is approved in the chat."""
    settings = chat_settings_collection.find_one({"_id": chat_id}, {"approved_users": 1})
    return bool(settings and user_id in settings.get("approved_users", []))

async def is_user_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """Checks if a user is an admin by any method (Telegram, Bot, or Anon)."""
    if user_id == 1087968824: # Anonymous Admin
        settings = chat_settings_collection.find_one({"_id": chat_id}, {"allow_anon_admin": 1})
        if settings and settings.get("allow_anon_admin", False):
            return True
    return await is_user_telegram_admin(context, chat_id, user_id) or is_user_bot_admin(chat_id, user_id)
