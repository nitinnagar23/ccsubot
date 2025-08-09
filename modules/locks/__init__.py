import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import lock_command, unlock_command, list_locks, check_locks
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Locks module."""
    admin_cmds = {
        "lock": "Lock one or more items to restrict them to admins.",
        "unlock": "Unlock one or more items for everyone.",
        "locks": "List currently locked items.",
        "lockwarns": "Toggle warnings for users who send locked items.",
        "locktypes": "Show the list of all lockable items.",
        "allowlist": "Whitelist a URL, user, or sticker pack from being locked.",
        "rmallowlist": "Remove an item from the allowlist.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Locks", "category": "admin", "help": help_text}

    HELP_REGISTRY["Locks"] = admin_cmds
    
    handlers = {
        "lock": lock_command,
        "unlock": unlock_command,
        "locks": list_locks,
    }
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add the main listener. It runs in an early group to catch content
    # before other modules (like Filters) can process it.
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_locks), group=5)
