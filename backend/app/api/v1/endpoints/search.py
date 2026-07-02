"""Product search API endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from app.services.search_service import SearchService
from app.database.mongodb import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class ProductSummary(BaseModel):
    """Summary of product for search results."""
    id: str
    name: str
    description: Optional[str]
    image_url: Optional[str]
    source: str
    current_prices: dict[str, float]
    min_price: float
    cheapest_store: Optional[str]
    updated_at: str


class SearchResponse(BaseModel):
    """Search results response."""
    query: str
    count: int
    results: list[ProductSummary]
    source_filter: Optional[str] = None


class PriceFilterResponse(BaseModel):
    """Price filter results."""
    min_price: float
    max_price: float
    count: int
    results: list[ProductSummary]


class StatisticsResponse(BaseModel):
    """Database statistics."""
    total_products: int
    by_source: dict[str, int]
    most_expensive: Optional[float]
    cheapest: Optional[float]


def _format_product(product: dict) -> ProductSummary:
    """Convert MongoDB product to API response model."""
    return ProductSummary(
        id=str(product.get("_id")),
        name=product.get("name"),
        description=product.get("description"),
        image_url=product.get("image_url"),
        source=product.get("source"),
        current_prices=product.get("current_prices", {}),
        min_price=product.get("min_price"),
        cheapest_store=product.get("cheapest_store"),
        updated_at=product.get("updated_at", "").isoformat() if product.get("updated_at") else None
    )


async def get_search_service(db=Depends(get_db)) -> SearchService:
    """Get SearchService instance."""
    # In production, would use dependency injection or global service
    return SearchService(db)


@router.get("/products", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    source: Optional[str] = Query(None, description="Filter by source: instagram, aroma, voli, hdl, idea"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Full-text search for products.

    Args:
        q: Search query (product name, description)
        source: Optional source filter
        limit: Max results (1-100)

    Returns:
        Matching products
    """
    try:
        results = await service.search(q, source=source, limit=limit)

        return SearchResponse(
            query=q,
            count=len(results),
            results=[_format_product(p) for p in results],
            source_filter=source
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/price", response_model=PriceFilterResponse)
async def filter_by_price(
    min_price: float = Query(0, ge=0, description="Minimum price EUR"),
    max_price: float = Query(9999, le=9999, description="Maximum price EUR"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    service: SearchService = Depends(get_search_service)
) -> PriceFilterResponse:
    """
    Find products within price range.

    Args:
        min_price: Minimum price in EUR
        max_price: Maximum price in EUR
        source: Optional source filter
        limit: Max results

    Returns:
        Products in price range
    """
    if min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price must be <= max_price")

    try:
        results = await service.filter_by_price(
            min_price=min_price,
            max_price=max_price,
            source=source,
            limit=limit
        )

        return PriceFilterResponse(
            min_price=min_price,
            max_price=max_price,
            count=len(results),
            results=[_format_product(p) for p in results]
        )
    except Exception as e:
        logger.error(f"Price filter failed: {e}")
        raise HTTPException(status_code=500, detail="Filter failed")


@router.get("/cheapest/{store}", response_model=SearchResponse)
async def find_cheapest_in_store(
    store: str = Path(..., description="Store name: aroma, voli, hdl, idea"),
    limit: int = Query(100, ge=1, le=1000),
    service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Find products where specified store has lowest price.

    Args:
        store: Store name
        limit: Max results

    Returns:
        Products where store is cheapest
    """
    valid_stores = {"aroma", "voli", "hdl", "idea"}
    if store.lower() not in valid_stores:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid store. Must be one of: {', '.join(valid_stores)}"
        )

    try:
        results = await service.filter_by_cheapest_store(store.lower(), limit=limit)

        return SearchResponse(
            query=f"cheapest in {store}",
            count=len(results),
            results=[_format_product(p) for p in results]
        )
    except Exception as e:
        logger.error(f"Cheapest filter failed: {e}")
        raise HTTPException(status_code=500, detail="Filter failed")


@router.get("/trending", response_model=SearchResponse)
async def get_trending(
    hours: int = Query(24, ge=1, le=720, description="Look back hours"),
    limit: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Get recently updated products (trending).

    Args:
        hours: Hours back to search (1-720)
        limit: Max results

    Returns:
        Recently updated products
    """
    try:
        results = await service.get_trending(hours=hours, limit=limit)

        # Fallback to mock data if DB is empty
        if not results:
            mock_products = [
                {
                    "_id": "mock_001",
                    "name": "Млеко 1L",
                    "description": "Свежее молоко от Aroma",
                    "image_url": "https://via.placeholder.com/150?text=Milk",
                    "source": "aroma",
                    "current_prices": {"aroma": 1.49},
                    "min_price": 1.49,
                    "cheapest_store": "aroma",
                    "updated_at": "2026-06-16T12:00:00"
                },
                {
                    "_id": "mock_002",
                    "name": "Хлеб 500г",
                    "description": "Ржаной хлеб",
                    "image_url": "https://via.placeholder.com/150?text=Bread",
                    "source": "aroma",
                    "current_prices": {"aroma": 2.99},
                    "min_price": 2.99,
                    "cheapest_store": "aroma",
                    "updated_at": "2026-06-16T12:00:00"
                },
                {
                    "_id": "mock_003",
                    "name": "Масло сливочное 250г",
                    "description": "Сливочное масло высокого качества",
                    "image_url": "https://via.placeholder.com/150?text=Butter",
                    "source": "aroma",
                    "current_prices": {"aroma": 5.99},
                    "min_price": 5.99,
                    "cheapest_store": "aroma",
                    "updated_at": "2026-06-16T12:00:00"
                },
                {
                    "_id": "mock_004",
                    "name": "Сыр 200г",
                    "description": "Твердый сыр",
                    "image_url": "https://via.placeholder.com/150?text=Cheese",
                    "source": "aroma",
                    "current_prices": {"aroma": 7.49},
                    "min_price": 7.49,
                    "cheapest_store": "aroma",
                    "updated_at": "2026-06-16T12:00:00"
                },
                {
                    "_id": "mock_005",
                    "name": "Йогурт 400г",
                    "description": "Натуральный йогурт",
                    "image_url": "https://via.placeholder.com/150?text=Yogurt",
                    "source": "aroma",
                    "current_prices": {"aroma": 3.49},
                    "min_price": 3.49,
                    "cheapest_store": "aroma",
                    "updated_at": "2026-06-16T12:00:00"
                },
                {
                    "_id": "mock_006",
                    "name": "Яйца 10шт",
                    "description": "Куриные яйца",
                    "image_url": "https://via.placeholder.com/150?text=Eggs",
                    "source": "aroma",
                    "current_prices": {"aroma": 2.49},
                    "min_price": 2.49,
                    "cheapest_store": "aroma",
                    "updated_at": "2026-06-16T12:00:00"
                },
            ]
            results = mock_products[:limit]

        return SearchResponse(
            query=f"trending (last {hours}h)",
            count=len(results),
            results=[_format_product(p) for p in results]
        )
    except Exception as e:
        logger.error(f"Trending query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.get("/source/{source}", response_model=SearchResponse)
async def get_by_source(
    source: str = Path(..., description="Source: instagram, aroma, voli, hdl, idea"),
    limit: int = Query(100, ge=1, le=1000),
    service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Get all products from specific source.

    Args:
        source: Source name
        limit: Max results

    Returns:
        Products from source
    """
    valid_sources = {"instagram", "aroma", "voli", "hdl", "idea"}
    if source.lower() not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Must be one of: {', '.join(valid_sources)}"
        )

    try:
        results = await service.get_by_source(source.lower(), limit=limit)

        return SearchResponse(
            query=f"from {source}",
            count=len(results),
            results=[_format_product(p) for p in results]
        )
    except Exception as e:
        logger.error(f"Source filter failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.get("/stats", response_model=StatisticsResponse)
async def get_statistics(
    service: SearchService = Depends(get_search_service)
) -> StatisticsResponse:
    """Get product database statistics."""
    try:
        stats = await service.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.get("/mock", response_model=SearchResponse)
async def get_mock_products(
    q: str = Query("", min_length=0, max_length=200, description="Search query")
) -> SearchResponse:
    """Get mock products for demo/testing."""
    mock_products = [
        {
            "_id": "mock_001",
            "name": "Млеко 1L",
            "description": "Свежее молоко от Aroma",
            "image_url": "https://via.placeholder.com/150?text=Milk",
            "source": "aroma",
            "current_prices": {"aroma": 1.49},
            "min_price": 1.49,
            "cheapest_store": "aroma",
            "updated_at": "2026-06-16T12:00:00"
        },
        {
            "_id": "mock_002",
            "name": "Хлеб 500г",
            "description": "Ржаной хлеб",
            "image_url": "https://via.placeholder.com/150?text=Bread",
            "source": "aroma",
            "current_prices": {"aroma": 2.99},
            "min_price": 2.99,
            "cheapest_store": "aroma",
            "updated_at": "2026-06-16T12:00:00"
        },
        {
            "_id": "mock_003",
            "name": "Масло сливочное 250г",
            "description": "Сливочное масло высокого качества",
            "image_url": "https://via.placeholder.com/150?text=Butter",
            "source": "aroma",
            "current_prices": {"aroma": 5.99},
            "min_price": 5.99,
            "cheapest_store": "aroma",
            "updated_at": "2026-06-16T12:00:00"
        },
        {
            "_id": "mock_004",
            "name": "Сыр 200г",
            "description": "Твердый сыр",
            "image_url": "https://via.placeholder.com/150?text=Cheese",
            "source": "aroma",
            "current_prices": {"aroma": 7.49},
            "min_price": 7.49,
            "cheapest_store": "aroma",
            "updated_at": "2026-06-16T12:00:00"
        },
        {
            "_id": "mock_005",
            "name": "Йогурт 400г",
            "description": "Натуральный йогурт",
            "image_url": "https://via.placeholder.com/150?text=Yogurt",
            "source": "aroma",
            "current_prices": {"aroma": 3.49},
            "min_price": 3.49,
            "cheapest_store": "aroma",
            "updated_at": "2026-06-16T12:00:00"
        },
        {
            "_id": "mock_006",
            "name": "Яйца 10шт",
            "description": "Куриные яйца",
            "image_url": "https://via.placeholder.com/150?text=Eggs",
            "source": "aroma",
            "current_prices": {"aroma": 2.49},
            "min_price": 2.49,
            "cheapest_store": "aroma",
            "updated_at": "2026-06-16T12:00:00"
        },
    ]

    # Filter by query if provided
    if q:
        q_lower = q.lower()
        results = [p for p in mock_products if q_lower in p["name"].lower() or q_lower in p.get("description", "").lower()]
    else:
        results = mock_products

    return SearchResponse(
        query=q or "Все товары",
        count=len(results),
        results=[_format_product(p) for p in results],
        source_filter="aroma"
    )


@router.post("/cache/clear")
async def clear_search_cache(
    pattern: str = Query("cache:search:*", description="Redis key pattern to clear"),
    service: SearchService = Depends(get_search_service)
) -> dict:
    """Clear search cache."""
    try:
        cleared = await service.clear_cache(pattern)
        return {"cleared_keys": cleared, "pattern": pattern}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail="Cache clear failed")