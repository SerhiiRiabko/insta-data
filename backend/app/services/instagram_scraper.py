"""Scrape recent Instagram posts for price data."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from instagrapi.types import Media, MediaOembed
from app.services.instagram_auth import InstagramSessionManager
from app.services.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)


class InstagramPostScraper:
    """Scrape Instagram posts and extract price data."""

    def __init__(self, session_manager: InstagramSessionManager, price_extractor: PriceExtractor):
        self.session = session_manager
        self.extractor = price_extractor
        self.client = None

    async def scrape_recent_posts(self, username: str, hours_back: int = 48) -> list[dict]:
        """
        Scrape recent posts from Instagram account.

        Args:
            username: Instagram username to scrape
            hours_back: How many hours back to search (default: 48)

        Returns:
            List of post data with extracted prices
        """
        self.client = self.session.get_client()
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        try:
            user = self.client.user_info_by_username(username)
            logger.info(f"Scraping posts for @{username} (ID: {user.pk})")
        except Exception as e:
            logger.error(f"Failed to get user info for @{username}: {e}")
            return []

        posts = []
        try:
            # Get recent posts (limit to avoid rate limiting)
            medias = self.client.user_medias(user.pk, amount=100)

            for media in medias:
                # Skip if too old
                if media.taken_at < cutoff_time:
                    logger.info(f"Stopping scrape: post older than {hours_back}h")
                    break

                # Skip stories, reels, videos without images
                if not hasattr(media, 'media_type') or media.media_type not in [1, 8]:  # photo or carousel
                    continue

                post_data = await self._process_post(media, username, user.pk)
                if post_data:
                    posts.append(post_data)

            logger.info(f"Scraped {len(posts)} posts from @{username}")
            return posts

        except Exception as e:
            logger.error(f"Error scraping posts from @{username}: {e}")
            return posts

    async def _process_post(self, media, username: str, user_id: int) -> Optional[dict]:
        """Extract post metadata and images."""
        try:
            images = []

            # Single photo
            if media.media_type == 1:  # photo
                if media.image_url:
                    images.append(media.image_url)

            # Carousel (multiple images)
            elif media.media_type == 8:  # carousel
                if hasattr(media, 'resources') and media.resources:
                    for resource in media.resources:
                        if resource.media_type == 1 and hasattr(resource, 'image_url'):
                            images.append(resource.image_url)

            if not images:
                return None

            post_data = {
                "media_id": str(media.pk),
                "username": username,
                "user_id": user_id,
                "caption": media.caption or "",
                "images": images,
                "posted_at": media.taken_at.isoformat() if hasattr(media, 'taken_at') else None,
                "likes": media.like_count if hasattr(media, 'like_count') else 0,
                "comments": media.comment_count if hasattr(media, 'comment_count') else 0,
                "source": "instagram"
            }

            return post_data

        except Exception as e:
            logger.error(f"Error processing post {media.pk}: {e}")
            return None

    async def process_posts(self, posts: list[dict]) -> list[dict]:
        """
        Process scraped posts: extract images, OCR, extract prices.

        Returns:
            List of products with extracted prices
        """
        products = []

        for post in posts:
            # Extract text from caption
            caption_text = post.get("caption", "")

            # Extract prices from images
            for image_url in post.get("images", []):
                try:
                    extracted = await self.extractor.extract_from_image_url(image_url)
                    if extracted and extracted.get("prices"):
                        # Create product from extracted data
                        product = {
                            "name": extracted.get("product_name", "Unknown"),
                            "description": caption_text[:500],  # Use caption as description
                            "category": extracted.get("category"),
                            "image_url": image_url,
                            "source": "instagram",
                            "prices": [
                                {
                                    "store": "instagram",
                                    "price": price["value"],
                                    "currency": price.get("currency", "EUR"),
                                    "timestamp": datetime.utcnow().isoformat()
                                }
                                for price in extracted["prices"]
                            ],
                            "metadata": {
                                "media_id": post["media_id"],
                                "username": post["username"],
                                "posted_at": post["posted_at"]
                            }
                        }
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Failed to extract from image {image_url}: {e}")

        logger.info(f"Extracted {len(products)} products from {len(posts)} posts")
        return products