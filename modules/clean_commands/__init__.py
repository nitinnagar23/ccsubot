import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import set_clean_command, keep_command, list_clean_command_types, clean_command_listener
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Clean Commands module."""
    admin_cmds = {
        "cleancommand": "Select command types to delete after use.",
        "keepcommand": "Select command types to stop deleting.",
        "cleancommandtypes": "List the different command types and their status.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "CleanCommands", "category": "admin", "help": help_text}

    HELP_REGISTRY["CleanCommands"] = admin_cmds
    
    handlers = {
        "cleancommand": set_clean_command,
        "keepcommand": keep_command,
        "cleancommandtypes": list_clean_command_types,
    }
    
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add the listener. The high group number ensures it runs AFTER 
    # the actual command handlers have finished their work.
    application.add_handler(MessageHandler(filters.COMMAND, clean_command_listener), group=20)
