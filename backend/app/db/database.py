import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from app.config import settings
from app.utils.logger import logger

class Database:
    client: AsyncIOMotorClient = None
    db = None
    is_connected: bool = False

db = Database()

async def connect_to_mongo():
    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            db.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=15000,
                socketTimeoutMS=15000
            )
            # Verify connection
            await db.client.admin.command('ping')
            
            # 1. Check default database in connection URI
            selected_db = None
            try:
                selected_db = db.client.get_default_database()
            except ConfigurationError:
                selected_db = None

            # 2. Case-insensitive database name matching to avoid MongoDB Atlas code 13297
            if selected_db is None or selected_db.name == "admin":
                target_name = settings.MONGODB_DB_NAME
                db_names = await db.client.list_database_names()
                matched_name = target_name
                for existing_name in db_names:
                    if existing_name.lower() == target_name.lower():
                        matched_name = existing_name
                        break
                selected_db = db.client[matched_name]

            db.db = selected_db
            db.is_connected = True
            logger.info(f"Successfully connected to MongoDB database '{db.db.name}'")
            return
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"MongoDB connection attempt {attempt} failed ({e}). Retrying in 2 seconds...")
                await asyncio.sleep(2)
            else:
                logger.warning(f"MongoDB connection failed after {max_retries} attempts ({e}). Operating in memory/fallback mode for sessions.")
                db.is_connected = False
                db.db = None

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection.")

def get_db():
    return db.db
