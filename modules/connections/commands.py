from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest

from utils.decorators import check_disabled
from utils.permissions import is_user_admin
from utils.context import resolve_target_chat_id

async def connect_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Connect to another chat to manage it remotely."""
    user = update.effective_user
    args = context.args
    
    if update.effective_chat.type != "private":
        await update.message.reply_text("You can only connect to chats from a private message with me.")
        return

    if not args:
        await update.message.reply_text("You need to provide a chat ID or username (e.g., -100123456 or @mygroup).")
        return

    target_chat_identifier = args[0]
    try:
        # Convert to int if it's a numeric ID
        if target_chat_identifier.lstrip('-').isdigit():
            target_chat_identifier = int(target_chat_identifier)
        target_chat = await context.bot.get_chat(target_chat_identifier)
    except BadRequest:
        await update.message.reply_text("Could not find that chat. Make sure the ID/username is correct and I am an admin there.")
        return

    # Security Check 1: User must be an admin in the target chat.
    if not await is_user_admin(context, target_chat.id, user.id):
        await update.message.reply_text(f"You don't have permission to connect to **{target_chat.title}** because you are not an admin there.", parse_mode=ParseMode.HTML)
        return
        
    # Security Check 2: Bot must be an admin in the target chat.
    try:
        me_member = await target_chat.get_member(context.bot.id)
        if me_member.status != ChatMemberStatus.ADMINISTRATOR:
            await update.message.reply_text(f"I am not an admin in **{target_chat.title}**, so I cannot be managed from here.", parse_mode=ParseMode.HTML)
            return
    except BadRequest:
         await update.message.reply_text(f"I don't seem to be a member of **{target_chat.title}**.", parse_mode=ParseMode.HTML)
         return

    # All checks passed, store the connection in user_data
    context.user_data['connected_chat_id'] = target_chat.id
    context.user_data['connected_chat_title'] = target_chat.title
    
    await update.message.reply_text(f"✅ Successfully connected to **{target_chat.title}** (`{target_chat.id}`).\nAll admin commands will now be sent to this chat.", parse_mode=ParseMode.HTML)

async def disconnect_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disconnect from the currently connected chat."""
    if 'connected_chat_id' in context.user_data:
        connected_title = context.user_data.get('connected_chat_title', 'the connected chat')
        # Save for /reconnect
        context.user_data['previous_connected_chat_id'] = context.user_data.pop('connected_chat_id')
        context.user_data['previous_connected_chat_title'] = context.user_data.pop('connected_chat_title', None)
            
        await update.message.reply_text(f"Disconnected from **{connected_title}**.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("You are not connected to any chat.")

async def reconnect_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reconnect to the last chat you were connected to."""
    if 'previous_connected_chat_id' in context.user_data:
        # Re-run the connect logic by faking the arguments
        context.args = [str(context.user_data['previous_connected_chat_id'])]
        await connect_chat(update, context)
    else:
        await update.message.reply_text("No previous connection found to reconnect to.")

async def connection_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the current connection status."""
    if 'connected_chat_id' in context.user_data:
        chat_id = context.user_data['connected_chat_id']
        chat_title = context.user_data.get('connected_chat_title', 'N/A')
        await update.message.reply_text(f"You are currently connected to:\n**{chat_title}** (`{chat_id}`)", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("You are not connected to any chat.")
