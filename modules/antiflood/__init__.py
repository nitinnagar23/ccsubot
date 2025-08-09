import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import set_flood, set_flood_mode, check_flood # Import handlers
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Antiflood module."""
    # Define admin commands
    admin_cmds = {
        "flood": "Get the current antiflood settings.",
        "setflood": "Set the number of consecutive messages to trigger antiflood.",
        "setfloodtimer": "Set timed antiflood (e.g., 10 messages in 30s).",
        "floodmode": "Set the punishment for flooding (ban/mute/kick/etc).",
        "clearflood": "Toggle deletion of flooding messages.",
    }
    
    # A map of commands to their actual handler functions
    # (Some commands like /floodstatus are not implemented in the snippet above for brevity)
    handlers = {
        "setflood": set_flood,
        "floodmode": set_flood_mode,
    }

    # Register all commands and add their handlers
    for cmd_name, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd_name] = {"module": "Antiflood", "category": "admin", "help": help_text}
        if cmd_name in handlers:
            handler_func = handlers[cmd_name]
            application.add_handler(CommandHandler(cmd_name, handler_func))
            application.add_handler(MessageHandler(
                filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
                handler_func
            ))
            
    HELP_REGISTRY["Antiflood"] = admin_cmds
    
    # Add the main message handler to check all messages
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_flood), group=10)
