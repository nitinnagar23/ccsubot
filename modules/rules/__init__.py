import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import rules_command, set_rules #, other_commands...
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Rules module."""
    COMMAND_REGISTRY["rules"] = {"module": "Rules", "category": "user", "help": "Check the current chat rules."}
    
    admin_cmds = {
        "setrules": "Set the rules for this chat.",
        "privaterules": "Toggle whether rules should be sent in private.",
        "resetrules": "Reset the chat rules to default.",
        "setrulesbutton": "Set the rules button name for the {rules} filling.",
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Rules", "category": "admin", "help": help_text}

    HELP_REGISTRY["Rules"] = {**{"rules": COMMAND_REGISTRY["rules"]["help"]}, **admin_cmds}
    
    handlers = {"rules": rules_command, "setrules": set_rules}
    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'), handler_func))
