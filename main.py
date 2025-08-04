import logging from telegram.ext import Application from config import TOKEN, OWNER_ID from modules import load_all_modules from utils.startup import startup_check

logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )

LOGGER = logging.getLogger(name)

async def main(): await startup_check()

application = Application.builder().token(TOKEN).build()

load_all_modules(application)

LOGGER.info("Bot started!")
await application.run_polling()

if name == 'main': import asyncio asyncio.run(m
ain())
