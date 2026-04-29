from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ ERROR: MONGO_URI not found in .env file")
else:
    print(f"🔗 Connecting to MongoDB")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ MongoDB Connected Successfully")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    print("Make sure:")
    print("  1. Your MongoDB cluster is active")
    print("  2. MONGO_URI in .env is correct")
    print("  3. Your IP is whitelisted in MongoDB Atlas")

db = client["agropredict"]
users_collection = db["users"]
recommendations_collection = db["recommendations"]