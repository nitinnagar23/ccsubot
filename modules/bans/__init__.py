import re
from telegram.ext import CommandHandler, MessageHandler, filters
from .commands import (
    ban, dban, sban, tban, unban,
    mute, dmute, smute, tmute, unmute,
    kick, dkick, skick, kickme
)
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Bans module, registering all moderation commands."""
    
    # Define commands and their properties
    commands_to_load = {
        "kickme": {"handler": kickme, "category": "user", "help": "Kicks the user who issues the command."},
        "ban": {"handler": ban, "category": "admin", "help": "Ban a user. Can be temporary."},
        "dban": {"handler": dban, "category": "admin", "help": "Reply to ban a user and delete their message."},
        "sban": {"handler": sban, "category": "admin", "help": "Silently ban a user."},
        "tban": {"handler": tban, "category": "admin", "help": "Temporarily ban a user (duration required)."},
        "unban": {"handler": unban, "category": "admin", "help": "Unban a user."},
        "mute": {"handler": mute, "category": "admin", "help": "Mute a user. Can be temporary."},
        "dmute": {"handler": dmute, "category": "admin", "help": "Reply to mute a user and delete their message."},
        "smute": {"handler": smute, "category": "admin", "help": "Silently mute a user."},
        "tmute": {"handler": tmute, "category": "admin", "help": "Temporarily mute a user (duration required)."},
        "unmute": {"handler": unmute, "category": "admin", "help": "Unmute a user."},
        "kick": {"handler": kick, "category": "admin", "help": "Kick a user (they can rejoin)."},
        "dkick": {"handler": dkick, "category": "admin", "help": "Reply to kick a user and delete their message."},
        "skick": {"handler": skick, "category": "admin", "help": "Silently kick a user."}
    }

    for cmd_name, info in commands_to_load.items():
        # Register command in the central registry
        COMMAND_REGISTRY[cmd_name] = {"module": "Bans", "category": info["category"], "help": info["help"]}
        
        # Add handlers for both '/' and '!' prefixes
        application.add_handler(CommandHandler(cmd_name, info["handler"]))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            info["handler"]
        ))
    
    HELP_REGISTRY["Bans"] = {cmd: info["help"] for cmd, info in commands_to_load.items()}
