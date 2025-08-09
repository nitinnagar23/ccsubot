import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import start_command
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Start module."""
    COMMAND_REGISTRY["start"] = {
        "module": "Start",
        "category": "user",
        "help": "Starts the bot and shows the welcome message."
    }
    HELP_REGISTRY["Start"] = {"start": "Starts the bot."}
    
    cmd_name = "start"
    handler_func = start_command
    
    # The /start command is special and usually doesn't use a '!' prefix
    application.add_handler(CommandHandler(cmd_name, handler_func))
