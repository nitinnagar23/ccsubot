import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup 
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import add_filter, stop_filter, list_filters, check_filters, stopall_command, stopall_callback
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Filters module."""
    admin_cmds = {
        "filter": "Set a reply for a certain trigger.",
        "filters": "List all active filters.",
        "stop": "Stop a filter from replying.",
        "stopall": "Stop all filters in the chat.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Filters", "category": "admin", "help": help_text}

    HELP_REGISTRY["Filters"] = admin_cmds
    
    handlers = {
        "filter": add_filter,
        "filters": list_filters,
        "stop": stop_filter,
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add the main listener for all text and command messages
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.COMMAND) & ~filters.UpdateType.EDITED,
        check_filters
    ), group=12)
