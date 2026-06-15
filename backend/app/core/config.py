"""
Insta-data Backend — Configuration Settings
Loaded from .env file using Pydantic
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # 🔵 Backend config
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = True
    environment: str = "development"  # development, staging, production
    secret_key: str = "dev-secret-key-change-in-production"

    # 🗄️ MongoDB
    mongodb_url: str = "mongodb://admin:admin@mongo:27017"
    mongodb_db: str = "insta_data"
    mongodb_user: str = "admin"
    mongodb_password: str = "admin"

    # 🐘 PostgreSQL
    postgres_url: str = "postgresql://admin:admin@postgres:5432/insta_data_history"
    postgres_user: str = "admin"
    postgres_password: str = "admin"
    postgres_db: str = "insta_data_history"

    # 🔴 Redis
    redis_url: str = "redis://redis:6379"
    redis_db: int = 0

    # 📝 Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    # 🔐 Security
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # 🌐 CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # 📱 Instagram
    instagram_email: str = "Niobium_Runas"
    instagram_password: str = ""
    instagram_session_file: str = "./instagram_session.json"

    # ⚙️ Scraper settings
    scraper_timeout: int = 30
    scraper_retry_attempts: int = 3
    scraper_instagram_max_posts: int = 100
    scraper_update_interval_hours: int = 24
    scraper_instagram_enabled: bool = True
    scraper_aroma_enabled: bool = True
    scraper_voli_enabled: bool = True
    scraper_hdl_enabled: bool = True
    scraper_idea_enabled: bool = True

    # 🖼️ Image processing
    image_max_width: int = 500
    image_max_height: int = 500
    image_quality: int = 85
    image_format: str = "jpeg"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()