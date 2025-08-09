# Modular Telegram Bot

![Replit](https://img.shields.io/badge/Hosted%20on-Replit-blue?style=for-the-badge&logo=replit)

A powerful, modular Telegram group management bot built with Python, MongoDB, and hosted on Replit. This bot is designed for scalability and easy feature extension.

## 🌟 Features

This bot is packed with features, organized into logical modules:

* **Core Moderation:** Bans, Mutes, Kicks, Warnings, Purges, Reports.
* **Advanced Security:** Anti-Raid, Anti-Flood, Misban (Anti-Betrayal), CAPTCHA.
* **Content Control:** Locks, Blocklists, Force Subscribe, Clean Service Messages.
* **Engagement & Fun:** Gamification (XP/Levels), AI Q&A, Games (Quiz, etc.), Echo.
* **Utility & Management:** Notes, Rules, Pinning, Greetings, Import/Export, Log Channels, and much more.
* **Powerful Admin Tools:** Remote chat management via `/connect`, command disabling, and a nested settings panel.

## 🚀 Setup & Installation

To run your own instance of this bot, follow these steps:

1.  **Fork this Repository** on GitHub or clone it.
2.  **Create a Replit Project:** Import the repository into a new Python Replit.
3.  **Set up MongoDB:** Create a free cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and get your connection URI.
4.  **Configure Secrets:** In the Replit "Secrets" tab, add the following environment variables:
    * `BOT_TOKEN`: Your bot token from @BotFather.
    * `MONGO_URI`: Your MongoDB connection string.
    * `BOT_OWNERS`: A comma-separated list of numeric owner User IDs.
    * `GEMINI_API_KEY`: Your free API key from Google AI Studio for the `/ask` command.
    .
5.  **Install Dependencies:** Run `pip install -r requirements.txt` in the Replit Shell.
6.  **Run:** Click the "Run" button in Replit. Use a service like [UptimeRobot](https://uptimerobot.com/) to ping the bot's web URL to keep it online 24/7.

## Usage

All bot configuration is handled through commands directly in your Telegram chat. Start by adding the bot to your group and promoting it to an administrator.

- Use `/help` to discover commands.
- Use the interactive `/settings` panel to configure modules.

---
*This bot was built with the assistance of Google's Gemini.*
