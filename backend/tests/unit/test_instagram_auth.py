"""Unit tests for InstagramSessionManager"""

import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from app.services.instagram_auth import InstagramSessionManager


@pytest.fixture
def mock_settings():
    """Mock settings"""
    settings = MagicMock()
    settings.INSTAGRAM_EMAIL = "test_user"
    settings.INSTAGRAM_PASSWORD = "test_pass"
    settings.INSTAGRAM_SESSION_FILE = "/tmp/test_session.json"
    return settings


@pytest.fixture
def session_manager(mock_settings):
    """Create InstagramSessionManager with mocked settings"""
    with patch('app.services.instagram_auth.settings', mock_settings):
        return InstagramSessionManager()


class TestSessionFilePersistence:
    """Test session file save/load operations"""

    def test_ensure_session_dir_creates_directory(self, session_manager):
        """Test that session directory is created"""
        with patch('app.services.instagram_auth.Path.mkdir') as mock_mkdir:
            session_manager._ensure_session_dir()
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_load_session_from_file_not_exists(self, session_manager):
        """Test loading session when file doesn't exist"""
        with patch('app.services.instagram_auth.Path.exists', return_value=False):
            result = session_manager._load_session_from_file()
            assert result is None

    def test_load_session_from_file_exists(self, session_manager):
        """Test loading valid session file"""
        session_data = {
            "user_id": "123456",
            "username": "test_user"
        }

        with patch('app.services.instagram_auth.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(session_data))):
                result = session_manager._load_session_from_file()
                assert result == session_data

    def test_load_session_file_corrupted(self, session_manager):
        """Test loading corrupted session file"""
        with patch('app.services.instagram_auth.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                result = session_manager._load_session_from_file()
                assert result is None

    def test_save_session_to_file(self, session_manager):
        """Test saving session to file"""
        session_data = {"user_id": "123456"}

        with patch('app.services.instagram_auth.Path.mkdir'):
            with patch('builtins.open', mock_open()) as mock_file:
                session_manager._save_session_to_file(session_data)
                mock_file.assert_called_once()
                # Verify JSON was written
                handle = mock_file()
                written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
                assert '"user_id": "123456"' in written_data


class TestSessionCreation:
    """Test session creation and loading"""

    @pytest.mark.asyncio
    async def test_load_cached_session_valid(self, session_manager):
        """Test loading valid cached session"""
        cached_session = {"user_id": "123456", "username": "test_user"}

        with patch.object(session_manager, '_load_session_from_file', return_value=cached_session):
            with patch.object(session_manager, '_ensure_session_dir'):
                with patch('app.services.instagram_auth.Client') as MockClient:
                    mock_client = MagicMock()
                    MockClient.return_value = mock_client
                    mock_client.set_settings = MagicMock()
                    mock_client.get_me = AsyncMock(return_value=MagicMock(pk=123))

                    client = session_manager.load_or_create_session()

                    assert client is not None
                    mock_client.set_settings.assert_called_once_with(cached_session)
                    mock_client.get_me.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_cached_session_invalid(self, session_manager):
        """Test handling of invalid cached session"""
        cached_session = {"old": "data"}

        with patch.object(session_manager, '_load_session_from_file', return_value=cached_session):
            with patch.object(session_manager, '_ensure_session_dir'):
                with patch('app.services.instagram_auth.Client') as MockClient:
                    mock_client = MagicMock()
                    MockClient.return_value = mock_client

                    # First call fails (invalid session), second succeeds (new login)
                    mock_client.set_settings = MagicMock()
                    mock_client.get_me = AsyncMock(side_effect=[Exception("Invalid"), MagicMock(pk=123)])
                    mock_client.login = AsyncMock()
                    mock_client.get_settings = MagicMock(return_value={"new": "session"})

                    with patch.object(session_manager, '_save_session_to_file'):
                        with patch('app.services.instagram_auth.Path.unlink'):
                            client = session_manager.load_or_create_session()

                    assert client is not None

    @pytest.mark.asyncio
    async def test_load_no_cached_session_create_new(self, session_manager):
        """Test creating new session when none cached"""
        with patch.object(session_manager, '_load_session_from_file', return_value=None):
            with patch.object(session_manager, '_ensure_session_dir'):
                with patch('app.services.instagram_auth.Client') as MockClient:
                    mock_client = MagicMock()
                    MockClient.return_value = mock_client
                    mock_client.login = AsyncMock()
                    mock_client.get_settings = MagicMock(return_value={"new": "session"})

                    with patch.object(session_manager, '_save_session_to_file') as mock_save:
                        client = session_manager.load_or_create_session()

                        assert client is not None
                        mock_client.login.assert_called_once_with("test_user", "test_pass")
                        mock_save.assert_called_once()


class TestSessionInvalidation:
    """Test session invalidation"""

    def test_invalidate_session(self, session_manager):
        """Test session invalidation"""
        session_manager.client = MagicMock()

        with patch('app.services.instagram_auth.Path.unlink'):
            session_manager.invalidate_session()

            assert session_manager.client is None


class TestGetClient:
    """Test get_client method"""

    def test_get_client_already_loaded(self, session_manager):
        """Test getting already loaded client"""
        mock_client = MagicMock()
        session_manager.client = mock_client

        with patch.object(session_manager, 'load_or_create_session') as mock_load:
            client = session_manager.get_client()

            assert client == mock_client
            mock_load.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_client_not_loaded(self, session_manager):
        """Test getting client when not loaded"""
        session_manager.client = None

        with patch.object(session_manager, 'load_or_create_session', return_value=MagicMock()):
            client = session_manager.get_client()

            assert client is not None