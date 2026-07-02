"""SQLAlchemy ORM models for PostgreSQL."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PriceHistory(Base):
    """Price history records for analytics and trending."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(24), nullable=False, index=True)  # MongoDB ObjectId as string
    product_name = Column(String(500), nullable=False)
    store = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Composite indexes
    __table_args__ = (
        Index('idx_product_store_timestamp', 'product_id', 'store', 'timestamp'),
        Index('idx_store_timestamp', 'store', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, store={self.store}, price={self.price})>"


class ScraperLog(Base):
    """Logs for scraper runs."""

    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_name = Column(String(50), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(20), nullable=False)  # running, success, failed
    products_found = Column(Integer, default=0)
    products_saved = Column(Integer, default=0)
    errors = Column(String(2000))  # Serialized error messages
    duration_seconds = Column(Float)

    __table_args__ = (
        Index('idx_scraper_timestamp', 'scraper_name', 'start_time'),
    )

    def __repr__(self):
        return f"<ScraperLog(scraper={self.scraper_name}, status={self.status})>"