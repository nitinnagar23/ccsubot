from datetime import datetime, timedelta
from telegram import ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from .time import humanize_delta

async def execute_punishment(
    context: ContextTypes.DEFAULT_TYPE, 
    chat_id: int, 
    user_id: int, 
    mode: str, 
    duration_seconds: int = 0
) -> tuple[bool, str]:
    """
    Executes a moderation action (ban, kick, mute, etc.) on a user.
    This is a centralized function to be used by Bans, Warnings, Locks, etc.
    
    Returns a tuple of (success_status, action_string).
    """
    action_string = ""
    try:
        if mode == "ban":
            await context.bot.ban_chat_member(chat_id, user_id)
            action_string = "banned"
        elif mode == "kick":
            # Kicking is a temporary ban for ~45 seconds, allowing immediate rejoin
            await context.bot.ban_chat_member(chat_id, user_id, until_date=datetime.now() + timedelta(seconds=45))
            action_string = "kicked"
        elif mode == "mute":
            # Mute indefinitely
            await context.bot.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
            action_string = "muted"
        elif mode in ["tban", "tmute"]:
            if duration_seconds <= 0:
                return False, "Temporary action requires a positive duration."
                
            until_date = datetime.now() + timedelta(seconds=duration_seconds)
            duration_str = humanize_delta(timedelta(seconds=duration_seconds))
            if mode == "tban":
                await context.bot.ban_chat_member(chat_id, user_id, until_date=until_date)
                action_string = f"banned for {duration_str}"
            else:  # tmute
                await context.bot.restrict_chat_member(
                    chat_id, user_id, 
                    ChatPermissions(can_send_messages=False), 
                    until_date=until_date
                )
                action_string = f"muted for {duration_str}"
        else:
            return False, f"Invalid punishment mode: {mode}"

        return True, action_string
        
    except BadRequest as e:
        # This often happens if the bot lacks permissions or tries to moderate another admin.
        return False, f"Failed: {e.message}"
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"
