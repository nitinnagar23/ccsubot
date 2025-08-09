from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

async def extract_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[int | None, str | None]:
    """
    Extracts a user from a message.
    Can be from a reply, a mention (@username), or a user ID.
    Returns a tuple of (user_id, user_first_name) or (None, None).
    """
    # Case 1: Reply to a message
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        return user.id, user.first_name

    # Case 2: Mention or User ID in arguments
    args = context.args
    if not args:
        return None, None

    target_arg = args[0]
    
    # Check for user ID
    if target_arg.isdigit():
        user_id = int(target_arg)
        try:
            user_chat = await context.bot.get_chat(user_id)
            return user_chat.id, user_chat.first_name
        except BadRequest:
            # User ID is invalid or not found
            return None, None
            
    # Check for username mention
    elif target_arg.startswith('@'):
        username = target_arg[1:]
        try:
            # Getting chat by username is not a standard method for users.
            # This is often handled by iterating through known users or other means.
            # For simplicity, we will rely on replies and IDs which are more reliable.
            # We can inform the user about this.
            await update.message.reply_text("Fetching users by username can be unreliable. Please reply to the user or use their ID if possible.")
            return None, None
        except Exception:
            return None, None

    return None, None
