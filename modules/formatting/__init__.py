import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import markdown_help_command
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Formatting help module."""
    COMMAND_REGISTRY["markdownhelp"] = {
        "module": "Formatting",
        "category": "user",
        "help": "Get help on how to use markdown, buttons, and fillings."
    }
    HELP_REGISTRY["Formatting"] = {
        "markdownhelp": COMMAND_REGISTRY["markdownhelp"]["help"]
    }
    
    cmd_name = "markdownhelp"
    handler_func = markdown_help_command
    
    application.add_handler(CommandHandler(cmd_name, handler_func))
    application.add_handler(MessageHandler(
        filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
        handler_func
    ))
