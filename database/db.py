import os
import pymongo
from pymongo import MongoClient

# Get the MongoDB URI from Replit Secrets
MONGO_URI = os.environ.get('MONGO_URI')

# A simple error check
if not MONGO_URI:
    raise Exception("❌ MONGO_URI not found in environment variables! Please set it in Replit's Secrets.")

# Establish the connection
client = MongoClient(MONGO_URI)

# Select your database (you can name it whatever you want)
# Using a try-except block to check the connection.
try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB.")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")

db = client["MyModularTelegramBotDB"]

# You can define easy access to collections here if you like, but it's often
# cleaner to access them directly via the 'db' object in other modules,
# e.g., db["users"], db["notes"], etc.
