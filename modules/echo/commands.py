import asyncio
from telegram import Update, MessageEntity
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_core.registry import COMMAND_REGISTRY, HELP_REGISTRY
from utils.decorators import admin_only, owner_only
from utils.context import resolve_target_chat_id
from database.db import db

bot_chats_collection = db["bot_chats"]

# --- Helper to extract text and entities ---
def _extract_text_and_entities(message: Update.message):
    """Extracts the echo text and adjusts entity offsets."""
    text_to_echo = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []

    command_entity = next((e for e in entities if e.type == MessageEntity.BOT_COMMAND), None)
    if not command_entity:
        return None, None

    start_index = command_entity.offset + command_entity.length + 1
    
    final_text = text_to_echo[start_index:]
    
    adjusted_entities = []
    for entity in entities:
        if entity.offset >= start_index:
            adjusted_entities.append(
                MessageEntity(
                    type=entity.type, offset=entity.offset - start_index, length=entity.length,
                    url=entity.url, user=entity.user, language=entity.language,
                    custom_emoji_id=entity.custom_emoji_id
                )
            )
    
    return final_text, adjusted_entities

# --- Broadcast Background Task ---
async def _broadcast_task(context: ContextTypes.DEFAULT_TYPE, owner_chat_id: int, text: str, entities: list):
    """The background task that performs the broadcast."""
    all_chats = list(bot_chats_collection.find({}, {"_id": 1}))
    chat_ids = [chat["_id"] for chat in all_chats]
    
    if not chat_ids:
        await context.bot.send_message(owner_chat_id, "I'm not in any chats to broadcast to!")
        return

    success_count = 0
    failure_count = 0
    
    for chat_id in chat_ids:
        try:
            await context.bot.send_message(chat_id, text=text, entities=entities)
            success_count += 1
        except Exception as e:
            failure_count += 1
            print(f"Failed to broadcast to {chat_id}: {e}")
        await asyncio.sleep(0.1) # Avoid hitting API rate limits

    await context.bot.send_message(
        owner_chat_id,
        f"Broadcast finished.\n✅ Success: {success_count}\n❌ Failures: {failure_count}"
    )

# --- Command Handlers ---
@admin_only
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echoes text and formatting provided by an admin."""
    target_chat_id = await resolve_target_chat_id(update, context)
    text, entities = _extract_text_and_entities(update.message)
    
    if not text:
        await update.message.reply_text("There's nothing to echo!")
        return
        
    try:
        await update.message.delete()
    except:
        pass # Not enough permissions, or in a PM

    await context.bot.send_message(target_chat_id, text=text, entities=entities)

@owner_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcasts a message to all chats (as a background task)."""
    text, entities = _extract_text_and_entities(update.message)
    
    if not text:
        await update.message.reply_text("There's nothing to broadcast!")
        return
        
    await update.message.reply_text("✅ Starting broadcast in the background. I'll send another message when it's complete.")
    
    asyncio.create_task(
        _broadcast_task(context, update.effective_chat.id, text, entities)
    )
