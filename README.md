# My Telegram Bot

A powerful, modular Telegram bot built in Python to manage and enhance group chats.

## Features

This bot is built with a modular architecture and includes the following features:
- Admin Tools & Moderation (Bans, Warnings, Locks)
- Anti-Spam & Anti-Raid Protection
- Welcome Greetings, Rules, and Notes
- Gamification with an XP/Level System
- And many more!

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd TelegramBot
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your bot's credentials. Alternatively, if using Replit, use the built-in Secrets tool.
    ```
    BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    ADMIN_IDS="12345678,87654321" # Comma-separated list of super admin user IDs
    ```

5.  **Run the bot:**
    ```bash
    python main.py
    ```

## Project Structure

The bot is organized into a modular structure:
- `main.py`: The main entry point for the bot.
- `core/`: Contains the core logic, configuration, and keep-alive server.
- `modules/`: Each `.py` file represents a feature module with its own comman
- d handlers.
