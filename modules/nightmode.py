# bot/modules/nightmode.py

from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, time
from bot.utils.database import nightmode_db
from bot.utils.helpers import is_admin

@Client.on_message(filters.command(["nightmode", "!nightmode"]) & filters.group)
async def set_night_mode(client: Client, message: Message):
    if not await is_admin(client, message):
        return

    if len(message.command) < 3:
        return await message.reply("Usage: /nightmode HH:MM HH:MM (24h format)")

    try:
        start_time = datetime.strptime(message.command[1], "%H:%M").time()
        end_time = datetime.strptime(message.command[2], "%H:%M").time()
        await nightmode_db.set_night_mode(message.chat.id, start_time, end_time)
        await message.reply(f"🌙 Night Mode enabled from {start_time} to {end_time}")
    except ValueError:
        await message.reply("Invalid time format. Use HH:MM (24-hour format).")

@Client.on_message(filters.group)
async def enforce_night_mode(client: Client, message: Message):
    times = await nightmode_db.get_night_mode(message.chat.id)
    if not times:
        return

    now = datetime.now().time()
    start, end = times

    if start < end:
        if start <= now <= end:
            await message.delete()
    else:
        if now >= start or now <= end:
            await message.delete()
