"""PostgreSQL connection and initialization"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database session factory
SessionLocal = None


async def init_postgres_db():
    """Initialize PostgreSQL connection"""
    global SessionLocal

    try:
        engine = create_engine(
            settings.postgres_url,
            echo=settings.environment == "development",
            future=True,
        )

        SessionLocal = sessionmaker(
            bind=engine,
            class_=Session,
            expire_on_commit=False,
        )

        # Verify connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        logger.info("✅ PostgreSQL connected successfully")

    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        raise


def get_postgres_db():
    """Get PostgreSQL session"""
    if SessionLocal is None:
        raise RuntimeError("PostgreSQL not initialized. Call init_postgres_db() first.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()