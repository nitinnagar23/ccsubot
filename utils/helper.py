from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["telegram_bot"]

# Collections for various modules
notesdb = db.notes
filtersdb = db.filters
warnsdb = db.warnings
usersdb = db.users
chatdb = db.chatsettings
logdb = db.logchannels
xpdb = db.xp
repeatsdb = db.repeats
fsubdb = db.fsub
topicsdb = db.topics
miscdb = db.misc
