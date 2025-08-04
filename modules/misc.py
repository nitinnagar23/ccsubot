# bot/modules/misc.py

import time
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import START_TIME
from bot.utils.helpers import get_readable_time
from pyrogram.errors import FloodWait
import asyncio
import platform
import psutil

@Client.on_message(filters.command(["ping", "!ping"]))
async def ping(client: Client, message: Message):
    start = time.time()
    m = await message.reply("🏓 Pinging...")
    end = time.time()
    latency = (end - start) * 1000
    await m.edit(f"🏓 Pong! `{int(latency)}ms`")

@Client.on_message(filters.command(["uptime", "!uptime"]))
async def uptime(client: Client, message: Message):
    current = time.time()
    uptime_str = get_readable_time(int(current - START_TIME))
    await message.reply(f"🕒 Bot Uptime: `{uptime_str}`")

@Client.on_message(filters.command(["stats", "!stats"]))
async def bot_stats(client: Client, message: Message):
    try:
        process = psutil.Process()
        mem_info = process.memory_info()
        cpu_percent = psutil.cpu_percent(interval=1)
        ram_percent = psutil.virtual_memory().percent
        uptime = get_readable_time(int(time.time() - START_TIME))
        sys_platform = platform.system()
        await message.reply(
            f"📊 **Bot Stats**:\n"
            f"• Uptime: `{uptime}`\n"
            f"• Platform: `{sys_platform}`\n"
            f"• CPU Usage: `{cpu_percent}%`\n"
            f"• RAM Usage: `{ram_percent}%`\n"
            f"• Memory: `{mem_info.rss / 1024 ** 2:.2f} MB`"
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
