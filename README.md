# 🤖 CCS University Bot

A **modular, MongoDB-powered Telegram bot** with advanced group management, automation, and gamification features. Designed for scalability, flexibility, and ease of use — built with Python and python-telegram-bot.

---

## 🧱 Project Structure

ccsuniversitybot/
├── bot/                     # Core bot system
│   ├── config.py           # Centralized configuration
│   ├── decorators.py       # Admin/sudo permissions
│   ├── dispatcher.py       # Custom command routing (! or /)
│   ├── loader.py           # Plugin/module loader
│   ├── logging.py          # Logging system
│   ├── helpers/            # Utilities, MongoDB handler, etc.
│   └── core/               # Cache, checks, rate limiting
│
├── plugins/                # All modular features (independent files)
│   ├── admin.py
│   ├── warns.py
│   ├── filters.py
│   ├── ...
│
├── start.py                # Main entry point
├── run.sh                  # Safe launcher
├── requirements.txt
├── .env                    # Bot secrets and settings
├── README.md
└── .github/workflows/      # GitHub CI/CD configs

---

## 🚀 Getting Started

### 1. Clone the Bot

git clone https://github.com/youruser/ccsuniversitybot.git
cd ccsuniversitybot

### 2. Install Dependencies

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### 3. Configure `.env`

Copy the `.env.example` and set your bot token, Mongo URI, etc.

BOT_TOKEN=123456:ABCDEF
MONGO_URI=mongodb://localhost:27017/
DB_NAME=ccsubot
OWNER_ID=123456789
LOG_CHANNEL=-100987654321
SUPPORT_CHAT=@ccsubot_support

### 4. Run the Bot

bash run.sh

---

## ✨ Features Overview

| Module             | Description                                 |
|--------------------|---------------------------------------------|
| Admin Tools        | Promote/demote users, view admins           |
| Filters            | Trigger responses to words/phrases          |
| Notes              | Save and retrieve notes with media          |
| Warn System        | Issue and manage warnings                   |
| Repeated Notes     | Auto-post messages at intervals             |
| Purges             | Bulk delete messages easily                 |
| Gamification       | XP system with levels and leaderboard       |
| Force Subscribe    | Enforce joining a channel to use bot        |
| Logging            | Logs deleted/edited messages and actions    |
| Trivia / Games     | Fun games like trivia, quizzes, XP rewards  |
| Global Chat        | Cross-chat message forwarding               |
| Help System        | Paginated help and /start overview          |

---

## 🧪 Sample Plugin: `plugins/misc.py`

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.decorators import sudo_only
from bot.helpers.utils import get_readable_time
import time

start_time = time.time()

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime_duration = get_readable_time(time.time() - start_time)
    await update.message.reply_text(f"🤖 Bot has been running for: {uptime_duration}")

def __help__():
    return "➤ /uptime - Show bot's uptime.\n➤ /ping - Check bot's latency."

def __mod_name__():
    return "Misc"

def get_handlers():
    return [CommandHandler(["uptime", "ping"], uptime)]

---

## 📘 Usage Tips

- Use `!` or `/` as command prefix.
- All modules include help text viewable with `/help`.
- Admin/sudo checks prevent misuse.

---

## 📚 Help & Commands

Use `/help` to start the **interactive help system** — browse by module, each with a short summary and list of available commands. You can also run `/start` for a greeting and command tips.

---

## 💻 Deployment Options

Supports:
- Heroku (`Procfile` included)
- Docker (`Dockerfile` and compose coming soon)
- Manual VPS

---

## ✅ Todo / Planned

- Add Web Dashboard for managing data
- Admin Panel for group owners
- Redis + Mongo dual-layer caching

---

## 🧾 License

MIT License © 2025 [YourName]
