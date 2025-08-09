from telegram import Update
from telegram.ext import ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus

from database.db import db

# Use a dedicated collection for tracking which chats the bot is in.
bot_chats_collection = db["bot_chats"]

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler is triggered when the bot's own membership status changes in a chat.
    It automatically adds or removes the chat from the broadcast list.
    """
    # This update is a ChatMemberUpdated object, which has different fields
    my_member_update = update.my_chat_member
    if not my_member_update:
        return

    chat = my_member_update.chat
    new_status = my_member_update.new_chat_member.status
    
    # Check if the bot was added, promoted, or is just a member
    if new_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        # Bot was added to the chat, so we add its ID and title to our collection.
        # Using update_one with upsert=True is safe and efficient.
        bot_chats_collection.update_one(
            {"_id": chat.id},
            {"$set": {"title": chat.title}},
            upsert=True
        )
        print(f"Bot was added to or promoted in chat: {chat.title} ({chat.id})")
        
    # Check if the bot was kicked or left
    elif new_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
        # Bot was removed from the chat, so we delete it from our list.
        bot_chats_collection.delete_one({"_id": chat.id})
        print(f"Bot was removed from chat: {chat.title} ({chat.id})")


def load_module(application):
    """Loads the Bot Status module."""
    # This module has no user-facing commands, so it doesn't register
    # anything in the COMMAND_REGISTRY or HELP_REGISTRY.
    
    # It only adds a single, specialized handler.
    # The ChatMemberHandler.MY_CHAT_MEMBER filter ensures this only triggers
    # when the BOT'S OWN status changes.
    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
