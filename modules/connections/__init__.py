import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import connect_chat, disconnect_chat, reconnect_chat, connection_status
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Connections module."""
    # These are user commands, as they are intended for use in PM.
    # The commands themselves perform the necessary admin checks.
    user_cmds = {
        "connect": "Connect to a chat to manage it remotely (PM only).",
        "disconnect": "Disconnect from the current chat.",
        "reconnect": "Reconnect to the previously connected chat.",
        "connection": "See information about the currently connected chat.",
    }
    for cmd, help_text in user_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Connections", "category": "user", "help": help_text}

    HELP_REGISTRY["Connections"] = user_cmds
    
    handlers = {
        "connect": connect_chat,
        "disconnect": disconnect_chat,
        "reconnect": reconnect_chat,
        "connection": connection_status,
    }

    for cmd_name, handler_func in handlers.items():
        # These commands are decorated with @check_disabled in their definition
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
