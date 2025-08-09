import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import (
    runs_command, id_command, info_command, 
    donate_command, limits_command
)
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Miscellaneous module."""
    user_cmds = {
        "runs": "Respond with a randomly generated 'run away' string.",
        "id": "Get the ID of a user, group, or channel.",
        "info": "Get a user's info.",
        "donate": "Donate to the bot creator.",
        "limits": "Show some of the bot's operational limits."
    }
    for cmd, help_text in user_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Misc", "category": "user", "help": help_text}

    HELP_REGISTRY["Misc"] = user_cmds
    
    handlers = {
        "runs": runs_command, "id": id_command, "info": info_command,
        "donate": donate_command, "limits": limits_command
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
