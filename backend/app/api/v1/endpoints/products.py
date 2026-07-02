"""Product API endpoints for frontend integration."""

import logging
import hashlib
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime
from app.database.mongodb import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


# ============================================================================
# SCHEMAS
# ============================================================================

class StorePrice(BaseModel):
    """Price from a single store."""
    store: str
    price: Optional[float] = None


class ProductRow(BaseModel):
    """Product row for price matrix table."""
    id: str
    name: str
    unit: str
    prices: List[Optional[float]]  # [aroma, voli, hdl, idea]
    min_price: Optional[float]
    cheapest_store: Optional[str]


class PriceMatrixResponse(BaseModel):
    """Price comparison matrix response."""
    stores: List[dict]  # [{"name": "Aroma", "initial": "A", "color": "#e11d48"}, ...]
    products: List[ProductRow]
    updated_at: str
    total_products: int


class ProductListItem(BaseModel):
    """Product item for list view."""
    id: str
    name: str
    unit: str
    description: Optional[str]
    image_url: Optional[str]
    source: str
    prices: dict  # {"aroma": 1.49, "voli": 1.45, ...}
    min_price: float
    cheapest_store: Optional[str]


class ProductListResponse(BaseModel):
    """Product list response."""
    products: List[ProductListItem]
    total_count: int
    updated_at: str


# ============================================================================
# MOCK DATA (fallback when DB is empty)
# ============================================================================

MOCK_STORES = [
    {"name": "Aroma", "initial": "A", "color": "#e11d48"},
    {"name": "Voli", "initial": "V", "color": "#2563eb"},
    {"name": "HDL", "initial": "H", "color": "#d97706"},
    {"name": "IDEA", "initial": "I", "color": "#0891b2"},
]

MOCK_PRODUCTS = [
    {
        "id": "mock_001",
        "name": "Молоко / Молоко / Milk",
        "unit": "1 л",
        "prices": [1.49, 1.45, 1.52, 1.39],
    },
    {
        "id": "mock_002",
        "name": "Хлеб / Хліб / Bread",
        "unit": "500 г",
        "prices": [0.89, 0.95, 0.85, 0.92],
    },
    {
        "id": "mock_003",
        "name": "Яйца / Яйця / Eggs",
        "unit": "10 шт",
        "prices": [2.49, 2.39, 2.55, 2.45],
    },
    {
        "id": "mock_004",
        "name": "Сыр Гауда / Сир Гауда / Gouda cheese",
        "unit": "1 кг",
        "prices": [8.90, 9.20, 8.45, 8.99],
    },
    {
        "id": "mock_005",
        "name": "Бананы / Банани / Bananas",
        "unit": "1 кг",
        "prices": [1.29, 1.19, 1.35, 1.25],
    },
    {
        "id": "mock_006",
        "name": "Кофе молотый / Кава мелена / Ground coffee",
        "unit": "250 г",
        "prices": [4.49, 4.29, 4.59, 4.19],
    },
    {
        "id": "mock_007",
        "name": "Оливковое масло / Оливкова олія / Olive oil",
        "unit": "1 л",
        "prices": [6.99, 7.49, 6.79, 7.10],
    },
    {
        "id": "mock_008",
        "name": "Вода / Вода / Water",
        "unit": "1,5 л",
        "prices": [0.55, 0.59, 0.49, 0.52],
    },
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_cheapest(prices: List[Optional[float]]) -> tuple:
    """
    Calculate min price and cheapest store index.

    Returns:
        (min_price, cheapest_store_index)
    """
    valid_prices = [(p, i) for i, p in enumerate(prices) if p is not None]
    if not valid_prices:
        return None, -1

    min_price = min(p for p, _ in valid_prices)
    cheapest_idx = next(i for p, i in valid_prices if p == min_price)

    return min_price, cheapest_idx


def format_product_row(product: dict, stores: List[dict]) -> ProductRow:
    """Convert mock/DB product to ProductRow."""
    min_price, cheapest_idx = calculate_cheapest(product["prices"])

    return ProductRow(
        id=product["id"],
        name=product["name"],
        unit=product["unit"],
        prices=product["prices"],
        min_price=min_price,
        cheapest_store=stores[cheapest_idx]["name"] if cheapest_idx >= 0 else None,
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/matrix", response_model=PriceMatrixResponse)
async def get_price_matrix(
    lang: str = Query("ru", regex="^(ru|uk|en)$", description="Language: ru, uk, en"),
    db=Depends(get_db)
) -> PriceMatrixResponse:
    """
    Get price comparison matrix for landing page.

    Returns:
        - stores: store metadata (name, initial, color)
        - products: product rows with prices for each store
        - updated_at: last update timestamp
        - total_products: number of products

    Example:
        GET /api/v1/products/matrix?lang=uk
    """
    try:
        # Try to fetch from MongoDB
        products_collection = db.products
        products = await products_collection.find().limit(100).to_list(100)

        # If no data, use mock
        if not products:
            logger.info("No products in DB, using mock data")
            products = MOCK_PRODUCTS
            stores = MOCK_STORES
        else:
            stores = MOCK_STORES  # TODO: fetch from config

        # Format response
        product_rows = [format_product_row(p, stores) for p in products]

        return PriceMatrixResponse(
            stores=stores,
            products=product_rows,
            updated_at=datetime.utcnow().isoformat(),
            total_products=len(product_rows),
        )

    except Exception as e:
        logger.error(f"Failed to get price matrix: {e}")
        # Fallback to mock data
        stores = MOCK_STORES
        product_rows = [format_product_row(p, stores) for p in MOCK_PRODUCTS]

        return PriceMatrixResponse(
            stores=stores,
            products=product_rows,
            updated_at=datetime.utcnow().isoformat(),
            total_products=len(product_rows),
        )


@router.get("/list", response_model=ProductListResponse)
async def get_product_list(
    limit: int = Query(50, ge=1, le=1000, description="Max results"),
    skip: int = Query(0, ge=0, description="Skip N products"),
    db=Depends(get_db)
) -> ProductListResponse:
    """
    Get product list with prices.

    Returns:
        - products: list of products
        - total_count: total products in DB
        - updated_at: timestamp
    """
    try:
        products_collection = db.products

        # Fetch from DB
        db_products = await products_collection.find().skip(skip).limit(limit).to_list(limit)

        if not db_products:
            logger.info("No products in DB, using mock data")
            db_products = MOCK_PRODUCTS[:limit]

        # Format response
        items = []
        for p in db_products:
            item = ProductListItem(
                id=str(p.get("_id", p.get("id"))),
                name=p.get("name", ""),
                unit=p.get("unit", ""),
                description=p.get("description"),
                image_url=p.get("image_url"),
                source=p.get("source", "unknown"),
                prices=p.get("current_prices", {}),
                min_price=p.get("min_price", 0),
                cheapest_store=p.get("cheapest_store"),
            )
            items.append(item)

        # Get total count
        total = await products_collection.count_documents({})

        return ProductListResponse(
            products=items,
            total_count=total or len(MOCK_PRODUCTS),
            updated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to get product list: {e}")
        # Fallback to mock
        items = [
            ProductListItem(
                id=p["id"],
                name=p["name"],
                unit=p["unit"],
                description=None,
                image_url=None,
                source="mock",
                prices={},
                min_price=min(p["prices"]),
                cheapest_store="Mock Store",
            )
            for p in MOCK_PRODUCTS[:limit]
        ]

        return ProductListResponse(
            products=items,
            total_count=len(MOCK_PRODUCTS),
            updated_at=datetime.utcnow().isoformat(),
        )


@router.post("/seed")
async def seed_database(db=Depends(get_db)) -> dict:
    """
    Seed database with initial 8 mock products.

    WARNING: Clears existing products and inserts mock data.
    Use once to initialize database for testing.
    """
    try:
        products_collection = db.products
        now = datetime.utcnow()

        # Clear existing products
        cleared = await products_collection.delete_many({})
        logger.info(f"🗑️  Cleared {cleared.deleted_count} existing products")

        # Prepare documents for insertion
        products_to_insert = []

        for product in MOCK_PRODUCTS:
            min_price, cheapest_idx = calculate_cheapest(product["prices"])
            cheapest_store = STORES[cheapest_idx]["name"] if cheapest_idx >= 0 else None

            doc = {
                "name": product["name"],
                "unit": product["unit"],
                "description": None,
                "source": "seed",
                "category": None,
                "image_url": None,
                "current_prices": {
                    STORES[j]["name"]: price
                    for j, price in enumerate(product["prices"])
                },
                "min_price": min_price,
                "max_price": max(p for p in product["prices"] if p is not None),
                "cheapest_store": cheapest_store,
                "dedup_hash": hashlib.md5(
                    f"{product['name']}_seed".lower().encode()
                ).hexdigest(),
                "created_at": now,
                "updated_at": now,
            }
            products_to_insert.append(doc)

        # Insert all products
        result = await products_collection.insert_many(products_to_insert)
        logger.info(f"✅ Inserted {len(result.inserted_ids)} products")

        # Verify count
        count = await products_collection.count_documents({})

        return {
            "success": True,
            "message": "Database seeded with 8 mock products",
            "products_cleared": cleared.deleted_count,
            "products_inserted": len(result.inserted_ids),
            "total_in_db": count,
        }

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")