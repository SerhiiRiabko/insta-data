"""MongoDB connection and initialization"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client and database
_mongo_client: AsyncIOMotorClient = None
_mongo_db: AsyncIOMotorDatabase = None


async def init_mongo_db():
    """Initialize MongoDB connection"""
    global _mongo_client, _mongo_db

    try:
        _mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        _mongo_db = _mongo_client[settings.mongodb_db]

        # Verify connection
        await _mongo_db.command("ping")
        logger.info("✅ MongoDB connected successfully")

    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def close_mongo_db():
    """Close MongoDB connection"""
    global _mongo_client

    if _mongo_client:
        _mongo_client.close()
        logger.info("✅ MongoDB disconnected")


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    if _mongo_db is None:
        raise RuntimeError("MongoDB not initialized. Call init_mongo_db() first.")
    return _mongo_db


async def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency: get MongoDB database"""
    return get_mongo_db()