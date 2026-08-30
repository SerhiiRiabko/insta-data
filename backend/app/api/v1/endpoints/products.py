"""Product API endpoints for frontend integration."""

import asyncio
import logging
import hashlib
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime
from app.database.mongodb import get_db, get_mongo_db
from app.services.category_map import classify_group_category
from app.services.grocery_dictionary import translate_via_dictionary
from app.services.translation_service import (
    LOCALES_NEEDING_TRANSLATION,
    SUPPORTED_LOCALES,
    resolve_display_name,
)

LANG_REGEX = "^(" + "|".join(SUPPORTED_LOCALES) + ")$"

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

COUNTRY_REGEX = "^(ME|UA)$"

# Last-resort fallback for Montenegro if `db.stores` is empty/unreachable -
# kept for the same reason MOCK_PRODUCTS is: the live endpoints must degrade
# gracefully, never hard-fail, when Mongo is down. There is no Ukraine
# equivalent (no data exists yet for that country either way).
FALLBACK_STORES_ME = [
    {"name": "Aroma", "initial": "A", "color": "#e11d48"},
    {"name": "Voli", "initial": "V", "color": "#2563eb"},
    {"name": "HDL", "initial": "H", "color": "#d97706"},
    {"name": "IDEA", "initial": "I", "color": "#0891b2"},
]
MOCK_STORES = FALLBACK_STORES_ME  # kept for the two old callers that never took a country

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

async def get_stores_for_country(country: str) -> List[dict]:
    """Active stores for one country, from the admin-editable `db.stores`
    collection (Phase 4.3) - falls back to the hardcoded Montenegro list only
    if Mongo is empty/unreachable, so the price matrix never hard-fails."""
    from app.api.v1.endpoints.stores import _ensure_seeded

    try:
        db = get_mongo_db()
        await _ensure_seeded()
        docs = await asyncio.wait_for(
            db.stores.find({"country": country, "active": True}).sort("name", 1).to_list(length=50),
            timeout=5.0,
        )
        if docs:
            return [{"name": d["name"], "initial": d["initial"], "color": d["color"]} for d in docs]
    except Exception as e:
        logger.warning(f"get_stores_for_country({country}): falling back ({e})")

    return FALLBACK_STORES_ME if country == "ME" else []


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


def format_product_row(product: dict, stores: List[dict], lang: str = "ukr") -> ProductRow:
    """Convert mock/DB product to ProductRow. Resolves the display name via
    `name_i18n[lang]` if the product has been translated (Phase 4.6), falling
    back to the original scraped name otherwise."""
    min_price, cheapest_idx = calculate_cheapest(product["prices"])

    return ProductRow(
        id=product["id"],
        name=resolve_display_name(product, lang),
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
    lang: str = Query("ukr", regex=LANG_REGEX, description="UI locale: ukr, rus, mne, srb, bos, eng"),
    country: str = Query("ME", regex=COUNTRY_REGEX, description="ME (Montenegro) or UA (Ukraine)"),
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
        GET /api/v1/products/matrix?lang=ukr&country=ME
    """
    stores = await get_stores_for_country(country)
    try:
        # Try to fetch from MongoDB
        products_collection = db.products
        products = await products_collection.find({"country": country}).limit(100).to_list(100)

        # No data yet: Montenegro has curated mock data to fall back to;
        # other countries just show an empty matrix (real stores, no prices).
        if not products and country == "ME":
            logger.info("No products in DB, using mock data")
            products = MOCK_PRODUCTS
            stores = FALLBACK_STORES_ME

        # Format response
        product_rows = [format_product_row(p, stores, lang) for p in products]

        return PriceMatrixResponse(
            stores=stores,
            products=product_rows,
            updated_at=datetime.utcnow().isoformat(),
            total_products=len(product_rows),
        )

    except Exception as e:
        logger.error(f"Failed to get price matrix: {e}")
        if country != "ME":
            return PriceMatrixResponse(stores=stores, products=[], updated_at=datetime.utcnow().isoformat(), total_products=0)
        # Fallback to mock data
        stores = FALLBACK_STORES_ME
        product_rows = [format_product_row(p, stores, lang) for p in MOCK_PRODUCTS]

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
    lang: str = Query("ukr", regex=LANG_REGEX, description="UI locale: ukr, rus, mne, srb, bos, eng"),
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
                name=resolve_display_name(p, lang),
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



async def _persist_live_products(products: List[dict], country: str = "ME", stores: Optional[List[dict]] = None) -> None:
    """
    Upsert freshly-scraped products into MongoDB's `products` collection so
    `/matrix` can serve them without re-scraping, and keep a bounded price
    history per product for future trend charts.

    Best-effort: if MongoDB isn't connected, this silently no-ops - the live
    endpoint must keep working even without a database.

    Merges into the existing doc's `prices` rather than blanket-overwriting
    it: a store missing from THIS run's `prices[i]` (None) keeps its last
    known price instead of losing it. Without this, a single store having a
    bad scrape (e.g. temporarily rate-limited/blocked - happened to Сільпо
    for a stretch of this session) wipes out every group it used to
    contribute to on the very next live refresh, even though the store
    itself didn't actually stop carrying those products. `stores` (in the
    same order the `prices` arrays are indexed) is needed to recompute
    `cheapest_store` after a merge might change which index is cheapest.
    """
    try:
        db = get_mongo_db()
    except RuntimeError:
        return

    now = datetime.utcnow()
    collection = db.products
    store_names = [s["name"] for s in stores] if stores else None

    for product in products:
        prices = list(product["prices"])
        promo = list(product.get("promo") or [False] * len(prices))

        existing = await collection.find_one(
            {"id": product["id"], "country": country}, {"prices": 1, "promo": 1}
        )
        if existing:
            old_prices = existing.get("prices") or []
            old_promo = existing.get("promo") or []
            for i in range(len(prices)):
                if prices[i] is None and i < len(old_prices) and old_prices[i] is not None:
                    prices[i] = old_prices[i]
                    promo[i] = old_promo[i] if i < len(old_promo) else False

        valid_prices = [p for p in prices if p is not None and p > 0]
        min_price = min(valid_prices) if valid_prices else None
        cheapest_store = None
        if min_price is not None and store_names and len(store_names) == len(prices):
            cheapest_store = store_names[prices.index(min_price)]
        else:
            cheapest_store = product.get("cheapest_store")

        set_fields = {
            "id": product["id"],
            "name": product["name"],
            "unit": product["unit"],
            "prices": prices,
            "promo": promo,
            "image_url": product.get("image_url"),
            "min_price": min_price,
            "cheapest_store": cheapest_store,
            "category": product.get("category"),
            "country": country,
            "updated_at": now,
        }
        # Dictionary translation is free/deterministic - recompute on every
        # scrape so a re-scraped name always has an up to date name_i18n.
        for locale in LOCALES_NEEDING_TRANSLATION:
            translated = translate_via_dictionary(product["name"], locale)
            if translated:
                set_fields[f"name_i18n.{locale}"] = translated

        # Matched on (id, country), not just id: the same content hash could
        # in principle collide across two countries' independent catalogs,
        # and they must never overwrite each other's price row.
        await collection.update_one(
            {"id": product["id"], "country": country},
            {
                "$set": set_fields,
                "$push": {
                    "price_history": {
                        "$each": [{"date": now, "prices": prices}],
                        "$slice": -30,  # keep the last 30 snapshots per product
                    }
                },
            },
            upsert=True,
        )

    logger.info(f"Persisted {len(products)} live products ({country}) to MongoDB")


async def _persist_live_products_background(
    products: List[dict], country: str = "ME", stores: Optional[List[dict]] = None
) -> None:
    """
    Fire-and-forget wrapper around _persist_live_products().

    Mongo can be "connected" (client object exists) but unreachable (wrong
    host/DNS), in which case each write blocks for the driver's own socket
    timeout (~20-30s) before failing - awaiting that inline would blow past
    the frontend's request timeout for what should be a fast, best-effort
    side effect. Run it as a detached task with a hard cap instead, so a dead
    Mongo never slows down the live price matrix response.

    Timeout is generous (not 5s) because _persist_live_products now does one
    extra read per product (to merge prices - see its docstring), and a
    country's full catalog can be 1500+ products; this task doesn't block
    the HTTP response either way, so there's little cost to letting it run
    longer before giving up.
    """
    try:
        await asyncio.wait_for(_persist_live_products(products, country, stores), timeout=60.0)
    except Exception as e:
        logger.warning(f"Failed to persist live matrix to MongoDB: {e}")


async def _scrape_and_group_live(country: str = "ME") -> tuple[list, list]:
    """
    Run all registered scrapers for one country and fuzzy-group the results
    across stores. Shared by /matrix-live and /by-category so both endpoints
    scrape once each, with identical grouping.

    Returns (grouped, all_products) - grouped is ProductMatcherService's
    per-product-group list (each with prices_by_store/promo_by_store/etc.),
    all_products is the flat pre-grouping list (used only for counting).
    """
    from app.services.scrapers.orchestrator import ScraperOrchestrator
    from app.services.product_matcher import ProductMatcherService

    orchestrator = ScraperOrchestrator()
    orch_result = await orchestrator.run_all(country=country)

    if orch_result.get("status") == "failed":
        return [], []

    all_products = []
    for store_name, store_result in orch_result.get("by_store", {}).items():
        if store_result.get("status") == "success":
            for product in store_result.get("all_products", []):
                # Use the product's own store/vendor attribution, not the
                # scraper's dict key - a single scraper (e.g. cijene.me)
                # can supply prices for several different stores.
                vendor = product.get("source", store_name).lower()
                all_products.append({
                    "name": product.get("name", "Unknown"),
                    "source": vendor,
                    "category": product.get("category", "Other"),
                    "image_url": product.get("image_url"),
                    "current_prices": {vendor: product.get("price", 0)},
                    "is_promo": product.get("is_promo", False),
                })

    matcher = ProductMatcherService(fuzzy_threshold=85)
    grouped = matcher.group_products(all_products)
    return grouped, all_products


def _build_product_row(group: dict, stores: List[dict], lang: str = "ukr") -> dict:
    """Convert one ProductMatcherService group into the {id, name, unit,
    prices[], image_url, ...} shape the frontend price matrix expects, with
    `prices` aligned to the given stores' order. Freshly-scraped groups have
    no `name_i18n` cache yet, so `resolve_display_name` naturally falls back
    to `canonical_name` here until the group has gone through /matrix-cached
    and been translated (admin-triggered or lazy background translation)."""
    prices_by_store = group.get("prices_by_store", {})
    promo_by_store = group.get("promo_by_store", {})
    prices = [prices_by_store.get(store["name"].lower()) for store in stores]
    promo = [bool(promo_by_store.get(store["name"].lower())) for store in stores]
    min_price, cheapest_idx = calculate_cheapest(prices)
    image_url = next(
        (p.get("image_url") for p in group.get("products", []) if p.get("image_url")),
        None,
    )
    return {
        "id": group["id"],
        "name": resolve_display_name({"name": group["canonical_name"]}, lang),
        "unit": group["unit"],
        "prices": prices,
        "promo": promo,
        "min_price": min_price,
        "cheapest_store": stores[cheapest_idx]["name"] if cheapest_idx >= 0 else None,
        "image_url": image_url,
        "category": classify_group_category(group.get("category"), group.get("canonical_name", "")),
    }


@router.get("/matrix-live")
async def get_price_matrix_live(
    lang: str = Query("ukr", regex=LANG_REGEX, description="UI locale: ukr, rus, mne, srb, bos, eng"),
    country: str = Query("ME", regex=COUNTRY_REGEX, description="ME (Montenegro) or UA (Ukraine)"),
):
    stores = await get_stores_for_country(country)
    try:
        logger.info(f"Running live scraper orchestrator (country={country}) with product matching...")
        grouped, all_products = await _scrape_and_group_live(country)

        if not grouped and not all_products:
            return {"stores": stores, "products": [], "groups": [], "total_groups": 0, "total_products": 0}

        products = [_build_product_row(group, stores, lang) for group in grouped]

        asyncio.create_task(_persist_live_products_background(products, country, stores))

        return {
            "stores": stores,
            "products": products,
            "groups": grouped,
            "total_groups": len(grouped),
            "total_products": len(all_products),
            "updated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get live price matrix: {e}")
        return {"stores": stores, "products": [], "groups": [], "total_groups": 0, "total_products": 0}


@router.get("/by-category")
async def get_products_by_category(
    lang: str = Query("ukr", regex=LANG_REGEX, description="UI locale: ukr, rus, mne, srb, bos, eng"),
    country: str = Query("ME", regex=COUNTRY_REGEX, description="ME (Montenegro) or UA (Ukraine)"),
):
    """
    Same live scrape as /matrix-live (cijene.me for ME, АТБ/Сільпо/Varus for
    UA), but grouped into product-group buckets (Овочі, Фрукти, Молочка,
    Бакалія, Дитячі товари...) instead of a flat list - see
    app/services/category_map.py for the category -> Ukrainian-label mapping.
    """
    from app.services.category_map import category_sort_key

    stores = await get_stores_for_country(country)

    try:
        logger.info(f"Running live scraper orchestrator (country={country}) for category grouping...")
        grouped, all_products = await _scrape_and_group_live(country)

        if not grouped and not all_products:
            return {"stores": stores, "categories": [], "total_products": 0}

        buckets: dict[str, list] = {}
        for group in grouped:
            row = _build_product_row(group, stores, lang)
            buckets.setdefault(row["category"], []).append(row)

        categories = [
            {"name": name, "count": len(products), "products": products}
            for name, products in sorted(buckets.items(), key=lambda kv: category_sort_key(kv[0]))
        ]

        asyncio.create_task(
            _persist_live_products_background(
                [p for cat in categories for p in cat["products"]], country, stores
            )
        )

        return {
            "stores": stores,
            "categories": categories,
            "total_products": len(all_products),
            "updated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get products by category: {e}")
        return {"stores": stores, "categories": [], "total_products": 0}


@router.get("/matrix-cached")
async def get_price_matrix_cached(
    lang: str = Query("ukr", regex=LANG_REGEX, description="UI locale: ukr, rus, mne, srb, bos, eng"),
    country: str = Query("ME", regex=COUNTRY_REGEX, description="ME (Montenegro) or UA (Ukraine)"),
):
    """
    Default endpoint for page load: serves the last persisted scan from
    MongoDB instead of re-scraping cijene.me (which /matrix-live and
    /by-category do, taking ~10-15s). Real prices only change via the weekly
    scheduled refresh (see refresh_prices_job, wired up in app/main.py) or a
    manual call to /matrix-live (e.g. the "Оновити ціни" button).

    Falls back to mock data if Mongo is empty or unreachable - capped at 5s so
    an unreachable Mongo host never blocks the page load. `lang` resolves
    each product's `name_i18n[lang]` if it's been translated (Phase 4.6),
    else falls back to the original scraped name. Mock data only makes sense
    for Montenegro (the only country with curated mock rows); other countries
    with no persisted data yet get a real (empty) store list and `source:
    "empty"` instead, so the frontend can show "no data yet" rather than
    silently showing Montenegro's mock prices under the wrong country.
    """
    stores = await get_stores_for_country(country)
    docs: list = []
    try:
        db = get_mongo_db()
        docs = await asyncio.wait_for(
            db.products.find({"country": country}).sort("updated_at", -1).to_list(2000), timeout=5.0
        )
    except Exception as e:
        logger.warning(f"matrix-cached: falling back ({e})")

    if not docs:
        if country == "ME":
            return {
                "stores": FALLBACK_STORES_ME,
                "products": [format_product_row(p, FALLBACK_STORES_ME, lang).model_dump() for p in MOCK_PRODUCTS],
                "total_products": len(MOCK_PRODUCTS),
                "updated_at": None,
                "source": "mock",
            }
        return {"stores": stores, "products": [], "total_products": 0, "updated_at": None, "source": "empty"}

    products = [
        {
            "id": d["id"],
            "name": resolve_display_name(d, lang),
            "unit": d["unit"],
            "prices": d["prices"],
            "promo": d.get("promo"),
            "min_price": d.get("min_price"),
            "cheapest_store": d.get("cheapest_store"),
            "image_url": d.get("image_url"),
            "category": d.get("category"),
        }
        for d in docs
    ]
    latest_update = max((d["updated_at"] for d in docs if d.get("updated_at")), default=None)

    return {
        "stores": stores,
        "products": products,
        "total_products": len(products),
        "updated_at": latest_update.isoformat() if latest_update else None,
        "source": "cache",
    }


async def refresh_prices_job() -> None:
    """
    Full scrape-and-persist cycle for the weekly scheduled job (see
    app/main.py) - the same work /matrix-live does per-request, but awaited
    directly rather than fire-and-forget, since a background scheduler job
    has no HTTP response to protect from a slow Mongo write.

    Montenegro-only: cijene.me is the only scraper pipeline that exists.
    """
    try:
        logger.info("Scheduled price refresh: starting live scrape...")
        grouped, all_products = await _scrape_and_group_live()
        if not grouped and not all_products:
            logger.warning("Scheduled price refresh: scrape returned no products")
            return

        stores = await get_stores_for_country("ME")
        products = [_build_product_row(group, stores) for group in grouped]
        await _persist_live_products(products, "ME", stores)
        logger.info(f"Scheduled price refresh: persisted {len(products)} products")
    except Exception as e:
        logger.error(f"Scheduled price refresh failed: {e}")

