# bot/handlers/help.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.pagination import paginate_help

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    await paginate_help(client, message)
