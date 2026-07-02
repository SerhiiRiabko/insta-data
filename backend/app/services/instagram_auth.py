"""Instagram session management using instagrapi."""

import json
import logging
from pathlib import Path
from typing import Optional
from instagrapi import Client
from instagrapi.types import UserShort
from app.core.config import settings

logger = logging.getLogger(__name__)


class InstagramSessionManager:
    """Manage Instagram session lifecycle with file-based persistence."""

    def __init__(self):
        self.session_file = Path(settings.INSTAGRAM_SESSION_FILE)
        self.email = settings.INSTAGRAM_EMAIL
        self.password = settings.INSTAGRAM_PASSWORD
        self.client: Optional[Client] = None

    def _ensure_session_dir(self) -> None:
        """Create session directory if it doesn't exist."""
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_session_from_file(self) -> Optional[dict]:
        """Load session data from JSON file."""
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session file: {e}")
            return None

    def _save_session_to_file(self, session_data: dict) -> None:
        """Save session data to JSON file."""
        self._ensure_session_dir()
        try:
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session saved to {self.session_file}")
        except Exception as e:
            logger.error(f"Failed to save session file: {e}")

    def load_or_create_session(self) -> Client:
        """Load existing session or create new one via login."""
        self._ensure_session_dir()

        # Try to load cached session
        session_data = self._load_session_from_file()
        if session_data:
            logger.info("Loading cached Instagram session")
            self.client = Client()
            try:
                self.client.set_settings(session_data)
                # Verify session is still valid
                self.client.get_me()
                logger.info("Session restored successfully")
                return self.client
            except Exception as e:
                logger.warning(f"Cached session invalid: {e}. Creating new session.")
                self.session_file.unlink(missing_ok=True)

        # Create new session via login
        logger.info(f"Creating new Instagram session for {self.email}")
        self.client = Client()
        try:
            self.client.login(self.email, self.password)
            logger.info("Instagram login successful")

            # Save session
            session_data = self.client.get_settings()
            self._save_session_to_file(session_data)

            return self.client
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            raise

    def get_client(self) -> Client:
        """Get authenticated Instagram client."""
        if self.client is None:
            self.load_or_create_session()
        return self.client

    def invalidate_session(self) -> None:
        """Invalidate current session (e.g., on 2FA error)."""
        self.client = None
        self.session_file.unlink(missing_ok=True)
        logger.info("Session invalidated and file deleted")

    def get_user_info(self) -> UserShort:
        """Get authenticated user info."""
        client = self.get_client()
        return client.get_me()