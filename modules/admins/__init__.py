import re
from telegram.ext import CommandHandler, MessageHandler, filters

from .commands import promote, demote, admin_list, admin_settings
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Admins module, registering commands and handlers."""
    # Define commands and their properties
    commands = {
        "promote": {"handler": promote, "help": "Promote a user to a bot admin."},
        "demote": {"handler": demote, "help": "Demote a user from being a bot admin."},
        "adminlist": {"handler": admin_list, "help": "List all admins in the chat."},
        "admincache": {"handler": admin_list, "help": "Update the cached list of admins (alias for /adminlist)."},
        "anonadmin": {"handler": admin_settings, "help": "Toggle permissions for anonymous admins."},
        "adminerror": {"handler": admin_settings, "help": "Toggle error messages for non-admin users."}
    }

    # Register all commands
    for cmd_name, cmd_info in commands.items():
        COMMAND_REGISTRY[cmd_name] = {"module": "Admins", "category": "admin", "help": cmd_info["help"]}
        
        # Add handlers for both '/' and '!' prefixes
        application.add_handler(CommandHandler(cmd_name, cmd_info["handler"]))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            cmd_info["handler"]
        ))
    
    # Populate the simple help registry
    HELP_REGISTRY["Admins"] = {cmd: info["help"] for cmd, info in commands.items()}
