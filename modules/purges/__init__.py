import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import delete_message, purge_command, spurge_command, purge_from, purge_to
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Purges module."""
    admin_cmds = {
        "purge": "Delete messages from the replied-to message until this one.",
        "spurge": "Silent version of /purge.",
        "del": "Delete the replied-to message.",
        "purgefrom": "Mark the start message for a ranged purge.",
        "purgeto": "Mark the end message and execute the ranged purge.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Purges", "category": "admin", "help": help_text}

    HELP_REGISTRY["Purges"] = admin_cmds
    
    handlers = {
        "del": delete_message,
        "purge": purge_command,
        "spurge": spurge_command,
        "purgefrom": purge_from,
        "purgeto": purge_to,
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
