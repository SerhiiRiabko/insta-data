from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    """Single price observation for a product at a store."""
    store: str = Field(..., description="Store name: aroma, voli, hdl, idea, instagram")
    price: float = Field(..., description="Price in EUR")
    currency: str = Field(default="EUR", description="Currency code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When price was recorded")


class ProductBase(BaseModel):
    """Base product information."""
    name: str = Field(..., description="Product name (e.g., 'Млеко 1L')", min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, description="Product description", max_length=2000)
    category: Optional[str] = Field(default=None, description="Product category", max_length=100)
    image_url: Optional[str] = Field(default=None, description="URL to product image")


class ProductCreate(ProductBase):
    """Product data for creation."""
    source: str = Field(..., description="Data source: instagram, aroma, voli, hdl, idea", max_length=50)
    prices: list[PricePoint] = Field(default_factory=list, description="Initial price observations")


class Product(ProductBase):
    """Full product model from MongoDB."""
    id: str = Field(..., alias="_id", description="MongoDB ObjectId as string")
    source: str = Field(..., description="Primary data source")
    dedup_hash: str = Field(..., description="MD5(name + source) for deduplication")
    prices: list[PricePoint] = Field(default_factory=list, description="All price observations")
    current_prices: dict[str, float] = Field(
        default_factory=dict,
        description="Latest price per store {store: price}"
    )
    min_price: float = Field(default=float('inf'), description="Cheapest price across all stores")
    max_price: float = Field(default=0, description="Most expensive price across all stores")
    cheapest_store: Optional[str] = Field(default=None, description="Store with minimum price")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When product was first added")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last price update")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Млеко 1L",
                "description": "Свіжа коров'яче молоко",
                "category": "Молочні продукти",
                "source": "aroma",
                "dedup_hash": "abc123def456",
                "prices": [
                    {
                        "store": "aroma",
                        "price": 1.39,
                        "currency": "EUR",
                        "timestamp": "2026-06-16T10:30:00"
                    }
                ],
                "current_prices": {
                    "aroma": 1.39,
                    "voli": 1.45,
                    "hdl": 1.35,
                    "idea": 1.50
                },
                "min_price": 1.35,
                "max_price": 1.50,
                "cheapest_store": "hdl",
                "created_at": "2026-06-15T08:00:00",
                "updated_at": "2026-06-16T10:30:00"
            }
        }


class ProductResponse(BaseModel):
    """Product response for API."""
    id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    image_url: Optional[str]
    source: str
    current_prices: dict[str, float]
    min_price: float
    cheapest_store: Optional[str]
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "Млеко 1L",
                "description": "Свіжа коров'яче молоко",
                "category": "Молочні продукти",
                "image_url": "https://example.com/milk.jpg",
                "source": "aroma",
                "current_prices": {
                    "aroma": 1.39,
                    "voli": 1.45,
                    "hdl": 1.35,
                    "idea": 1.50
                },
                "min_price": 1.35,
                "cheapest_store": "hdl",
                "updated_at": "2026-06-16T10:30:00"
            }
        }


class Store(BaseModel):
    """Store metadata for display."""
    name: str = Field(..., description="Store name")
    initial: str = Field(..., description="Short initial (1-2 chars)")
    color: str = Field(..., description="Hex color for UI")


class ProductGroup(BaseModel):
    """Grouped product across multiple stores."""
    id: str = Field(..., description="Hash ID of canonical name + category")
    canonical_name: str = Field(..., description="Normalized product name")
    category: str = Field(..., description="Product category")
    unit: str = Field(default="1x", description="Standardized unit (1L, 500g, etc.)")
    products: list[Product] = Field(default_factory=list, description="One product per store")
    prices_by_store: dict[str, float] = Field(default_factory=dict, description="Prices per store")
    min_price: float = Field(default=float('inf'), description="Cheapest price")
    max_price: float = Field(default=0, description="Most expensive price")
    cheapest_store: Optional[str] = Field(default=None, description="Store with lowest price")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123hash",
                "canonical_name": "Milk Kiš 1L",
                "category": "Dairy",
                "unit": "1L",
                "products": [],
                "prices_by_store": {
                    "Aroma": 1.49,
                    "Voli": 1.45,
                    "HDL": 1.52,
                    "IDEA": 1.39,
                    "Instagram": 1.89
                },
                "min_price": 1.39,
                "max_price": 1.89,
                "cheapest_store": "IDEA",
                "updated_at": "2026-07-03T10:00:00"
            }
        }


class ProductMatrix(BaseModel):
    """Response for price matrix endpoint."""
    stores: list[Store] = Field(default_factory=list, description="List of stores")
    groups: list[ProductGroup] = Field(default_factory=list, description="Grouped products")
    total_groups: int = Field(default=0, description="Number of unique product groups")
    total_products: int = Field(default=0, description="Total products across all stores")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update")