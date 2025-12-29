import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure we can import the script from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.client import SpotifyPlaylistBuilder


@pytest.fixture
def mock_spotify():
    """Mock the spotipy.Spotify client."""
    with patch("backend.core.client.spotipy.Spotify") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        # Mock successful authentication
        instance.current_user.return_value = {"id": "test_user_id"}
        yield instance


@pytest.fixture
def builder(mock_spotify):
    """Create a SpotifyPlaylistBuilder instance with mocked dependencies."""
    with (
        patch("backend.core.client.SpotifyOAuth"),
        patch("backend.core.client.MetadataVerifier") as mock_verifier_cls,
    ):
        # Setup mock verifier instance
        mock_verifier_instance = MagicMock()
        # Default behavior: verify_track_version returns False (neutral)
        mock_verifier_instance.verify_track_version.return_value = False
        mock_verifier_cls.return_value = mock_verifier_instance

        builder = SpotifyPlaylistBuilder("fake_client_id", "fake_client_secret")
        # Attach the mock to the builder for test access
        builder.metadata_verifier = mock_verifier_instance
        return builder


def pytest_addoption(parser):
    """Add CLI option to run CI tests."""
    parser.addoption("--run-ci", action="store_true", default=False, help="run tests marked for CI")


def pytest_configure(config):
    """Register the ci marker."""
    config.addinivalue_line("markers", "ci: mark test to run only in CI environment")


def pytest_collection_modifyitems(config, items):
    """Skip CI tests unless --run-ci is specified."""
    if config.getoption("--run-ci"):
        return

    skip_ci = pytest.mark.skip(reason="need --run-ci option to run")
    for item in items:
        if "ci" in item.keywords:
            item.add_marker(skip_ci)
