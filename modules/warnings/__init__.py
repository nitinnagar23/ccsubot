import re
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import warn_command, dwarn_command, swarn_command #, other_commands...
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Warnings module."""
    admin_cmds = {
        "warn": "Warn a user.", "dwarn": "Warn a user and delete their message.",
        "swarn": "Silently warn a user.", "warns": "See a user's warnings.",
        "rmwarn": "Remove a user's latest warning.", "resetwarn": "Reset all of a user's warnings.",
        "resetallwarns": "Delete all warnings in the chat.", "warnings": "Get the chat's warning settings.",
        "warnmode": "Set the punishment for exceeding the warn limit.", "warnlimit": "Set the number of warnings before punishment.",
        "warntime": "Set how long warnings should last before expiring."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Warnings", "category": "admin", "help": help_text}

    HELP_REGISTRY["Warnings"] = admin_cmds
    
    handlers = {
        "warn": warn_command, "dwarn": dwarn_command, "swarn": swarn_command,
        # ... add other handlers here ...
    }
    
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add callback handler for /resetallwarns if you implement it with confirmation
    # application.add_handler(CallbackQueryHandler(reset_all_warns_callback, pattern="^warn:resetall_"))
