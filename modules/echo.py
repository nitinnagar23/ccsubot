# bot/modules/echo.py

from pyrogram import Client, filters
from pyrogram.types import Message

from bot.utils.helpers import is_admin


@Client.on_message(filters.command(["echo", "!echo"]))
async def echo_command(client: Client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this command.")

    if len(message.command) < 2:
        return await message.reply("Please provide a message to echo.\nUsage: `/echo your message`")

    text = message.text.split(None, 1)[1]
    await message.reply(text)


@Client.on_message(filters.command(["necho", "!necho"]))
async def silent_echo(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 2:
        return

    await message.delete()
    text = message.text.split(None, 1)[1]
    await message.chat.send_message(text)
