import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .service import set_clean_msg, keep_msg, list_clean_msg_types
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Cleaning Bot Messages module."""
    admin_cmds = {
        "cleanmsg": "Select bot message types to delete after 5 minutes.",
        "keepmsg": "Select bot message types to stop deleting.",
        "cleanmsgtypes": "List available message types and their status.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "CleaningBotMessages", "category": "admin", "help": help_text}

    HELP_REGISTRY["CleaningBotMessages"] = admin_cmds
    
    handlers = {
        "cleanmsg": set_clean_msg,
        "keepmsg": keep_msg,
        "cleanmsgtypes": list_clean_msg_types,
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
