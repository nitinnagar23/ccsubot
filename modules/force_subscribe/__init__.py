import re
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import forcesub_add, check_subscription, verify_subscription_callback #, other_commands...
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Force Subscribe module."""
    admin_cmds = {
        "forcesubadd": "Add a channel to the required list.",
        "forcesubdel": "Remove a channel from the required list.",
        "forcesublist": "List all required channels.",
        "forcesubstatus": "Show if Force Subscribe is active and list channels.",
        "forcesuboff": "Disable force subscribe in the current group."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "ForceSubscribe", "category": "admin", "help": help_text}

    HELP_REGISTRY["ForceSubscribe"] = admin_cmds
    
    # Add command handlers
    # Using a dictionary for scalability
    handlers = {
        "forcesubadd": forcesub_add,
        # ... add other command handlers here ...
    }
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))

    # Add the core handlers
    # The listener runs in an early group to block messages before other modules act on them.
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_subscription), group=6)
    application.add_handler(CallbackQueryHandler(verify_subscription_callback, pattern="^forcesub:verify:"))
