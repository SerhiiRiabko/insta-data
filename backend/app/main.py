"""
Monte-Shop-Price Backend — FastAPI Application
Main entry point for the API
"""

import logging
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logger import setup_logging
from app.database.mongodb import init_mongo_db, close_mongo_db
from app.database.postgres import init_postgres_db
from app.api.v1.router import api_router
from app.api.v1.endpoints.products import refresh_prices_job

# Setup logging
setup_logging(log_level=settings.log_level)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Monte-Shop-Price Backend...")
    try:
        await init_mongo_db()
        logger.info("✅ MongoDB connected")

        # Text index backing SearchService's $text query — without it every
        # /search/products call throws, gets swallowed, and silently returns
        # zero results (including the name_i18n translated-name fallback,
        # which never gets a chance to run). idempotent: no-op if it exists.
        from app.database.mongodb import get_mongo_db
        await get_mongo_db().products.create_index(
            [("name", "text"), ("description", "text")],
            name="name_description_text",
        )
    except Exception as e:
        logger.warning(f"⚠️ MongoDB not available: {e}")

    try:
        await init_postgres_db()
        logger.info("✅ PostgreSQL connected")
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL not available: {e}")
        raise

    # Weekly price refresh: real cijene.me scrape runs automatically every
    # Monday 07:00 Kyiv time; the rest of the week the app serves the last
    # persisted scan from MongoDB (/products/matrix-cached). The "Оновити
    # ціни" button triggers the same scrape on demand via /products/matrix-live.
    scheduler.add_job(
        refresh_prices_job,
        trigger=CronTrigger(day_of_week="mon", hour=7, minute=0, timezone=ZoneInfo("Europe/Kyiv")),
        id="weekly_price_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("✅ Scheduler started: weekly price refresh (Mon 07:00 Europe/Kyiv)")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Monte-Shop-Price Backend...")
    scheduler.shutdown(wait=False)
    try:
        await close_mongo_db()
        logger.info("✅ MongoDB disconnected")
    except Exception as e:
        logger.error(f"❌ MongoDB disconnection failed: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Monte-Shop-Price API",
    description="Real-time price comparison for Montenegrin grocery stores",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Monte-Shop-Price API is running",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.backend_reload,
        log_level=settings.log_level.lower(),
    )