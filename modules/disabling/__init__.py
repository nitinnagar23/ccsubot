import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import (
    disable_command, enable_command, list_disableable, 
    list_disabled, set_disabled_delete, set_disable_admin
)
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Disabling module."""
    admin_cmds = {
        "disable": "Disable a command for users.",
        "enable": "Re-enable a disabled command.",
        "disableable": "List all disableable commands.",
        "disabledel": "Delete disabled commands when used.",
        "disableadmin": "Make disabled commands apply to admins too.",
        "disabled": "List all currently disabled commands."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Disabling", "category": "admin", "help": help_text}

    HELP_REGISTRY["Disabling"] = admin_cmds
    
    handlers = {
        "disable": disable_command, "enable": enable_command,
        "disableable": list_disableable, "disabled": list_disabled,
        "disabledel": set_disabled_delete, "disableadmin": set_disable_admin
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
