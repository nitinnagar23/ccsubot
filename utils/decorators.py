import re
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from .permissions import is_user_owner, is_user_creator, is_user_admin
from .context import resolve_target_chat_id
from bot_core.registry import COMMAND_REGISTRY
from database.db import db # <-- CORRECT: Import the main db object

# CORRECT: Get the collection from the db object
chat_settings_collection = db["chat_settings"]

def owner_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user and is_user_owner(user.id):
            return await func(update, context, *args, **kwargs)
        else: return
    return wrapped

def creator_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat
        if not user or not chat: return

        if await is_user_creator(context, chat.id, user.id):
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text("This command can only be used by the chat creator.")
            return
    return wrapped

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user: return

        target_chat_id = await resolve_target_chat_id(update, context)
        if await is_user_admin(context, target_chat_id, user.id):
            return await func(update, context, *args, **kwargs)
        else:
            settings = chat_settings_collection.find_one({"_id": update.effective_chat.id})
            send_error = settings.get("send_admin_error", True) if settings else True
            if send_error:
                await update.message.reply_text("Sorry, only admins can use this command.")
            return
    return wrapped

def check_disabled(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat = update.effective_chat
        user = update.effective_user
        if not chat or not user: return

        is_remote_command = ('connected_chat_id' in context.user_data and 
                             context.user_data['connected_chat_id'] != chat.id)
        if is_remote_command:
            return await func(update, context, *args, **kwargs)

        command_match = re.match(r"[!/](\w+)", update.message.text)
        if not command_match: return
        command = command_match.group(1).lower()

        settings = chat_settings_collection.find_one({"_id": chat.id}) or {}
        disabled_cmds = settings.get("disabled_commands", [])
        
        if "all" not in disabled_cmds and command not in disabled_cmds:
            return await func(update, context, *args, **kwargs)
        
        admins_are_disabled = settings.get("disable_admin", False)
        
        if not admins_are_disabled and await is_user_admin(context, chat.id, user.id):
            return await func(update, context, *args, **kwargs)
        
        if settings.get("disable_delete", False):
            try: await update.message.delete()
            except BadRequest: pass
        
        return
    return wrapped
