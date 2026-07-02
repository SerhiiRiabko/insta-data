"""MongoDB collection schema definitions and validation."""

MONGODB_PRODUCTS_SCHEMA = {
    "bsonType": "object",
    "required": ["name", "source", "dedup_hash"],
    "properties": {
        "_id": {"bsonType": "objectId"},
        "name": {
            "bsonType": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Product name"
        },
        "description": {
            "bsonType": ["string", "null"],
            "maxLength": 2000
        },
        "category": {
            "bsonType": ["string", "null"],
            "maxLength": 100
        },
        "image_url": {
            "bsonType": ["string", "null"],
            "pattern": "^https?://"
        },
        "source": {
            "bsonType": "string",
            "enum": ["instagram", "aroma", "voli", "hdl", "idea"],
            "description": "Primary data source"
        },
        "dedup_hash": {
            "bsonType": "string",
            "description": "MD5(name + source) for deduplication"
        },
        "prices": {
            "bsonType": "array",
            "items": {
                "bsonType": "object",
                "required": ["store", "price", "currency", "timestamp"],
                "properties": {
                    "store": {"bsonType": "string"},
                    "price": {"bsonType": "double"},
                    "currency": {"bsonType": "string"},
                    "timestamp": {"bsonType": "date"}
                }
            }
        },
        "current_prices": {
            "bsonType": "object",
            "additionalProperties": {"bsonType": "double"},
            "description": "Latest price per store: {store: price}"
        },
        "min_price": {
            "bsonType": "double",
            "description": "Minimum price across all stores"
        },
        "max_price": {
            "bsonType": "double",
            "description": "Maximum price across all stores"
        },
        "cheapest_store": {
            "bsonType": ["string", "null"],
            "description": "Store with minimum price"
        },
        "created_at": {
            "bsonType": "date",
            "description": "When product was first added"
        },
        "updated_at": {
            "bsonType": "date",
            "description": "Last update timestamp"
        }
    }
}

MONGODB_INDEXES = [
    {
        "name": "dedup_hash_unique",
        "keys": [("dedup_hash", 1)],
        "unique": True,
        "description": "Ensure product uniqueness by hash"
    },
    {
        "name": "source_index",
        "keys": [("source", 1)],
        "description": "Query by source (instagram, aroma, etc)"
    },
    {
        "name": "name_text_index",
        "keys": [("name", "text"), ("description", "text")],
        "description": "Full-text search on name and description"
    },
    {
        "name": "updated_at_index",
        "keys": [("updated_at", -1)],
        "description": "Sort by recency"
    },
    {
        "name": "price_range_index",
        "keys": [("min_price", 1), ("max_price", 1)],
        "description": "Query price range filters"
    },
    {
        "name": "ttl_index",
        "keys": [("updated_at", 1)],
        "expireAfterSeconds": 31536000,  # 365 days
        "description": "Auto-delete old products"
    }
]

POSTGRESQL_PRICE_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    product_id VARCHAR(24) NOT NULL,
    product_name VARCHAR(500) NOT NULL,
    store VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_store_timestamp
  ON price_history(product_id, store, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_store_timestamp
  ON price_history(store, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_timestamp
  ON price_history(timestamp DESC);
"""

REDIS_KEYS_PATTERNS = {
    "search_cache": "cache:search:{query}:{source}",
    "product_cache": "cache:product:{product_id}",
    "scraper_status": "scraper:status:{scraper_name}",
    "session_cache": "session:{session_id}"
}

REDIS_TTL = {
    "search_results": 300,  # 5 minutes
    "product_data": 600,    # 10 minutes
    "scraper_status": 60,   # 1 minute
}