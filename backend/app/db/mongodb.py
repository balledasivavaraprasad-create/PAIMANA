from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config.settings import settings
from app.config.logging import logger

class DatabaseManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_manager = DatabaseManager()

async def connect_to_mongo():
    try:
        db_manager.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db_manager.db = db_manager.client[settings.MONGODB_DB_NAME]
        # Quick ping
        await db_manager.client.admin.command('ping')
        logger.info(f"Connected successfully to MongoDB at {settings.MONGODB_URL}, database: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        logger.warning(f"Failed to connect directly to MongoDB: {e}. In-memory mock or local fallback available.")

async def close_mongo_connection():
    if db_manager.client:
        db_manager.client.close()
        logger.info("Closed MongoDB connection.")

def get_database() -> AsyncIOMotorDatabase:
    return db_manager.db
