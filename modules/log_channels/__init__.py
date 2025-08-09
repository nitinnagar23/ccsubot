import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .service import setlog_command_guide, handle_setlog_forward, unsetlog_command #, other_commands...
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Log Channels module."""
    admin_cmds = {
        "logchannel": "Get the name of the current log channel.",
        "setlog": "Set the log channel for this chat.",
        "unsetlog": "Unset the log channel for this chat.",
        "log": "Enable a log category.",
        "nolog": "Disable a log category.",
        "logcategories": "List all supported log categories."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "LogChannels", "category": "admin", "help": help_text}

    HELP_REGISTRY["LogChannels"] = admin_cmds
    
    # Handler for the initial /setlog command in the channel
    application.add_handler(CommandHandler("setlog", setlog_command_guide))
    # Handler for the forwarded message which performs the setup in the group
    application.add_handler(MessageHandler(filters.FORWARDED & filters.Regex(r'/setlog'), handle_setlog_forward))
    
    handlers = {"unsetlog": unsetlog_command} # Add other config handlers here
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
