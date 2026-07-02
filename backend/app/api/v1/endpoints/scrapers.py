"""Scraper management API endpoints."""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from app.services.orchestrator import ScraperOrchestrator
from app.database.mongodb import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrapers", tags=["scrapers"])

# Global orchestrator instance
_orchestrator: Optional[ScraperOrchestrator] = None


def get_orchestrator() -> ScraperOrchestrator:
    """Get scraper orchestrator instance."""
    if _orchestrator is None:
        raise HTTPException(
            status_code=500,
            detail="Scraper orchestrator not initialized"
        )
    return _orchestrator


async def init_orchestrator(db) -> None:
    """Initialize global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ScraperOrchestrator(db)
        await _orchestrator.start_scheduler()


class ScraperStatus(BaseModel):
    """Status of single scraper."""
    name: str
    status: str = Field(..., description="ready, running, completed, failed")
    last_run: Optional[str] = Field(default=None, description="ISO timestamp")
    duration: Optional[float] = Field(default=None, description="Last run duration in seconds")


class AllScraperStatus(BaseModel):
    """Status of all scrapers."""
    scrapers: Dict[str, ScraperStatus]
    scheduler_running: bool
    timestamp: str


class ScrapeRequest(BaseModel):
    """Request to run specific scraper."""
    store: str = Field(..., description="Store name: aroma, voli, hdl, idea, instagram")


class ScrapeResponse(BaseModel):
    """Response from scraper run."""
    store: str
    status: str = Field(..., description="success, failed")
    products_found: Optional[int] = None
    products_saved: Optional[int] = None
    posts_processed: Optional[int] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


@router.get("/status", response_model=AllScraperStatus)
async def get_scrapers_status(
    orchestrator: ScraperOrchestrator = Depends(get_orchestrator)
) -> AllScraperStatus:
    """Get status of all scrapers."""
    status = await orchestrator.get_status()
    return AllScraperStatus(**status)


@router.post("/run-all", response_model=Dict[str, Dict])
async def run_all_scrapers(
    orchestrator: ScraperOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Dict]:
    """
    Manually trigger all enabled scrapers (runs in parallel).

    ⚠️ This bypasses the scheduler and runs immediately.
    """
    logger.info("Manual trigger: running all scrapers")

    try:
        results = await orchestrator.run_all_scrapers()
        return results
    except Exception as e:
        logger.error(f"Failed to run all scrapers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraper run failed: {str(e)}"
        )


@router.post("/run", response_model=ScrapeResponse)
async def run_specific_scraper(
    request: ScrapeRequest,
    orchestrator: ScraperOrchestrator = Depends(get_orchestrator)
) -> ScrapeResponse:
    """
    Manually trigger specific scraper.

    Args:
        request.store: aroma, voli, hdl, idea, or instagram
    """
    store = request.store.lower()
    logger.info(f"Manual trigger: running {store} scraper")

    try:
        if store == "instagram":
            result = await orchestrator.run_instagram_scraper_only()
            return ScrapeResponse(
                store=store,
                status=result.get("status", "failed"),
                posts_processed=result.get("posts"),
                products_saved=result.get("products"),
                error=result.get("error")
            )
        elif store in ["aroma", "voli", "hdl", "idea"]:
            result = await orchestrator.run_store_scraper_only(store)
            return ScrapeResponse(
                store=store,
                status=result.get("status", "failed"),
                products_found=result.get("found"),
                products_saved=result.get("saved"),
                error=result.get("error")
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown store: {store}. Must be one of: aroma, voli, hdl, idea, instagram"
            )
    except Exception as e:
        logger.error(f"Failed to run {store} scraper: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraper failed: {str(e)}"
        )


@router.get("/schedule")
async def get_schedule(
    orchestrator: ScraperOrchestrator = Depends(get_orchestrator)
) -> Dict:
    """Get scraper schedule information."""
    if not orchestrator.scheduler:
        return {"error": "Scheduler not running"}

    jobs = []
    for job in orchestrator.scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "trigger": str(job.trigger),
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        "running": orchestrator.scheduler.running,
        "jobs": jobs
    }


@router.post("/pause")
async def pause_scheduler(
    orchestrator: ScraperOrchestrator = Depends(get_orchestrator)
) -> Dict:
    """Pause automatic scraper execution."""
    if orchestrator.scheduler:
        orchestrator.scheduler.pause()
        return {"status": "scheduler paused"}
    return {"error": "Scheduler not running"}


@router.post("/resume")
async def resume_scheduler(
    orchestrator: ScraperOrchestrator = Depends(get_orchestrator)
) -> Dict:
    """Resume automatic scraper execution."""
    if orchestrator.scheduler:
        orchestrator.scheduler.resume()
        return {"status": "scheduler resumed"}
    return {"error": "Scheduler not running"}


@router.get("/logs")
async def get_scraper_logs(
    store: Optional[str] = Query(None, description="Filter by store name"),
    limit: int = Query(100, ge=1, le=1000, description="Max records"),
    db=Depends(get_db)
) -> Dict:
    """Get scraper execution logs from PostgreSQL."""
    from sqlalchemy import select, desc
    from sqlalchemy.orm import Session
    from app.database.models import ScraperLog

    try:
        with Session(bind=db.engine) as session:
            query = select(ScraperLog)

            if store:
                query = query.where(ScraperLog.scraper_name == store.lower())

            logs = session.execute(
                query.order_by(desc(ScraperLog.start_time)).limit(limit)
            ).scalars().all()

            return {
                "count": len(logs),
                "logs": [
                    {
                        "scraper_name": log.scraper_name,
                        "status": log.status,
                        "start_time": log.start_time.isoformat(),
                        "end_time": log.end_time.isoformat() if log.end_time else None,
                        "products_found": log.products_found,
                        "products_saved": log.products_saved,
                        "duration_seconds": log.duration_seconds,
                        "errors": log.errors
                    }
                    for log in logs
                ]
            }
    except Exception as e:
        logger.error(f"Failed to fetch logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs")