import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import set_clean_service, keep_service, list_clean_service_types, clean_service_listener
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Clean Service module."""
    admin_cmds = {
        "cleanservice": "Select service message types to delete.",
        "keepservice": "Select service message types to stop deleting.",
        "nocleanservice": "Alias for /keepservice.",
        "cleanservicetypes": "List all available service message types and their status.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "CleanService", "category": "admin", "help": help_text}

    HELP_REGISTRY["CleanService"] = admin_cmds
    
    handlers = {
        "cleanservice": set_clean_service,
        "keepservice": keep_service,
        "nocleanservice": keep_service, # Alias
        "cleanservicetypes": list_clean_service_types,
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add the listener. The filters.StatusUpdate.ALL is a highly efficient
    # filter that only triggers on the exact messages we want to check.
    application.add_handler(MessageHandler(filters.StatusUpdate.ALL, clean_service_listener))
