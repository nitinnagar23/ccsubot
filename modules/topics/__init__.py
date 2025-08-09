import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import (
    set_action_topic, get_action_topic, new_topic, 
    rename_topic, close_topic
)
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Topics module."""
    admin_cmds = {
        "actiontopic": "Get the action topic for this forum.",
        "setactiontopic": "Set the current topic as the default action topic.",
        "newtopic": "Create a new topic.",
        "renametopic": "Rename the current topic.",
        "closetopic": "Close the current topic.",
        "reopentopic": "Reopen the current closed topic.",
        "deletetopic": "Delete the current topic (irreversible!)."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Topics", "category": "admin", "help": help_text}

    HELP_REGISTRY["Topics"] = admin_cmds

    handlers = {
        "setactiontopic": set_action_topic, "actiontopic": get_action_topic,
        "newtopic": new_topic, "renametopic": rename_topic,
        "closetopic": close_topic
        # ... add handlers for reopen and delete ...
    }
    
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
