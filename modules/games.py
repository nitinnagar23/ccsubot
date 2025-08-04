# modules/games.py

import random
from pyrogram import Client, filters
from pyrogram.types import Message

@Client.on_message(filters.command(["dice", "!dice"]))
async def roll_dice(client: Client, message: Message):
    await message.reply_dice("🎲")

@Client.on_message(filters.command(["coin", "!coin"]))
async def coin_flip(client: Client, message: Message):
    result = random.choice(["Heads", "Tails"])
    await message.reply(f"🪙 Coin Flip: **{result}**")

@Client.on_message(filters.command(["rps", "!rps"]))
async def rock_paper_scissors(client: Client, message: Message):
    result = random.choice(["🪨 Rock", "📄 Paper", "✂️ Scissors"])
    await message.reply(f"You got: **{result}**")

@Client.on_message(filters.command(["number", "!number"]))
async def guess_number(client: Client, message: Message):
    number = random.randint(1, 100)
    await message.reply(f"🎯 Your lucky number is: **{number}**")

@Client.on_message(filters.command(["8ball", "!8ball"]))
async def magic_8ball(client: Client, message: Message):
    responses = [
        "Yes.", "No.", "Maybe.", "Definitely.", "Absolutely not.",
        "Ask again later.", "Very likely.", "I don't think so."
    ]
    reply = random.choice(responses)
    await message.reply(f"🎱 {reply}")
