import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .qa import ask_command
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the AI module."""
    # Register the /ask command
    COMMAND_REGISTRY["ask"] = {
        "module": "AI",
        "category": "user",
        "help": "Ask a question to the AI."
    }
    HELP_REGISTRY["AI"] = {"ask": "Ask a question to the AI (e.g., /ask Who was the first person on the moon?)."}
    
    # Add handlers for both '/' and '!' prefixes
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(MessageHandler(
        filters.Regex(r'^!ask(\s|$)'),
        ask_command
    ))
