# bot/handlers/errors.py

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import Message
import traceback
import logging

logger = logging.getLogger(__name__)

@Client.on_message()
async def error_handler(_, message: Message):
    try:
        pass  # You can wrap your logic here if needed
    except RPCError as e:
        logger.error(f"RPCError: {e}")
    except Exception:
        logger.error("Unexpected error", exc_info=True)
