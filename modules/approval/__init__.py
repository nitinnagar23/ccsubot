import re
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .commands import (
    approval_status, approve_user, unapprove_user, 
    list_approved, unapprove_all_command, unapprove_all_callback
)
from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY

def load_module(application):
    """Loads the Approval module."""
    # User-facing command
    COMMAND_REGISTRY["approval"] = {"module": "Approval", "category": "user", "help": "Check a user's approval status."}
    
    # Admin commands
    admin_cmds = {
        "approve": "Approve a user to bypass certain restrictions.",
        "unapprove": "Revoke a user's approval.",
        "approved": "List all approved users.",
        "unapproveall": "Remove all users from the approved list."
    }
    for cmd, help_text in admin_cmds.items():
        COMMAND_REGISTRY[cmd] = {"module": "Approval", "category": "admin", "help": help_text}

    HELP_REGISTRY["Approval"] = {**{"approval": COMMAND_REGISTRY["approval"]["help"]}, **admin_cmds}
    
    # Map all commands to their handlers
    handlers = {
        "approval": approval_status,
        "approve": approve_user,
        "unapprove": unapprove_user,
        "approved": list_approved,
        "unapproveall": unapprove_all_command,
    }

    for cmd_name, handler_func in handlers.items():
        application.add_handler(CommandHandler(cmd_name, handler_func))
        application.add_handler(MessageHandler(
            filters.Regex(rf'^{re.escape("!")}{cmd_name}(\s|$)'),
            handler_func
        ))
        
    # Add the callback handler for the confirmation button
    application.add_handler(CallbackQueryHandler(unapprove_all_callback, pattern="^approval:unapprove_all_"))
