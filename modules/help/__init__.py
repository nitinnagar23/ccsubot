import re
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import help_command, help_callback
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the interactive Help module."""
    COMMAND_REGISTRY["help"] = {
        "module": "Help",
        "category": "user",
        "help": "Shows this interactive help menu."
    }
    HELP_REGISTRY["Help"] = {"help": "Shows this interactive help menu."}
    
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(
        filters.Regex(r'^!help(\s|$)'),
        help_command
    ))
    
    # This handler is the "brain" of the interactive menu
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help:"))
