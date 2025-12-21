import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

# Ensure we can import the script from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from spotify_playlist_builder import (
    SpotifyPlaylistBuilder,
    get_credentials_from_env,
    get_credentials_from_keyring,
    store_credentials_in_keyring,
    get_credentials,
    get_builder,
    CredentialSource,
    app,
)

runner = CliRunner()


@pytest.fixture
def mock_spotify():
    """Mock the spotipy.Spotify client."""
    with patch("spotify_playlist_builder.spotipy.Spotify") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        # Mock successful authentication
        instance.current_user.return_value = {"id": "test_user_id"}
        yield instance


@pytest.fixture
def builder(mock_spotify):
    """Create a SpotifyPlaylistBuilder instance with mocked dependencies."""
    with patch("spotify_playlist_builder.SpotifyOAuth"):
        return SpotifyPlaylistBuilder("fake_client_id", "fake_client_secret")


def test_get_credentials_from_env_success():
    """Test retrieving credentials from environment variables."""
    env_vars = {"SPOTIFY_CLIENT_ID": "test_id", "SPOTIFY_CLIENT_SECRET": "test_secret"}
    with patch("dotenv.load_dotenv"), patch.dict(os.environ, env_vars):
        cid, secret = get_credentials_from_env()
        assert cid == "test_id"
        assert secret == "test_secret"


def test_get_credentials_from_env_missing():
    """Test error when environment variables are missing."""
    with patch("dotenv.load_dotenv"), patch.dict(os.environ, {}, clear=True):
        with pytest.raises(Exception) as exc:
            get_credentials_from_env()
        assert "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not found" in str(exc.value)


def test_search_track_exact_match(builder, mock_spotify):
    """Test searching for a track that returns an exact match."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Test Song",
                    "artists": [{"name": "Test Artist"}],
                    "album": {"name": "Test Album"},
                    "uri": "spotify:track:123",
                }
            ]
        }
    }

    uri = builder.search_track("Test Artist", "Test Song")
    assert uri == "spotify:track:123"


def test_search_track_fuzzy_match(builder, mock_spotify):
    """Test the fuzzy matching logic selects the best candidate."""
    # Mock search returning multiple results
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Irrelevant Song",
                    "artists": [{"name": "Other Artist"}],
                    "album": {"name": "Album A"},
                    "uri": "spotify:track:999",
                },
                {
                    "name": "Target Song",
                    "artists": [{"name": "Target Artist"}],
                    "album": {"name": "Target Album"},
                    "uri": "spotify:track:456",
                },
            ]
        }
    }

    # Should match the second item based on string similarity
    uri = builder.search_track("Target Artist", "Target Song")
    assert uri == "spotify:track:456"


def test_create_playlist(builder, mock_spotify):
    """Test playlist creation parameters."""
    mock_spotify.user_playlist_create.return_value = {"id": "new_pid"}

    pid = builder.create_playlist("My List", "Description", public=False)

    assert pid == "new_pid"
    mock_spotify.user_playlist_create.assert_called_with(
        user="test_user_id", name="My List", public=False, description="Description"
    )


def test_add_tracks_to_playlist_batching(builder, mock_spotify):
    """Test that tracks are added in batches of 100."""
    with patch.object(builder, "search_track", return_value="spotify:track:1"):
        # Create 105 dummy tracks
        tracks = [{"artist": "A", "track": "B"}] * 105
        builder.add_tracks_to_playlist("pid", tracks)

        # Should be called twice: once for 100 tracks, once for 5 tracks
        assert mock_spotify.playlist_add_items.call_count == 2


def test_find_playlist_by_name_found(builder, mock_spotify):
    """Test finding a playlist that exists."""
    mock_spotify.current_user_playlists.return_value = {
        "items": [
            {"name": "Other Playlist", "owner": {"id": "test_user_id"}, "id": "other_id"},
            {"name": "My Playlist", "owner": {"id": "test_user_id"}, "id": "target_id"},
        ],
        "next": None,
    }

    pid = builder.find_playlist_by_name("My Playlist")
    assert pid == "target_id"


def test_find_playlist_by_name_pagination(builder, mock_spotify):
    """Test finding a playlist with pagination."""
    # Page 1: Not found
    page1 = {
        "items": [{"name": "P1", "owner": {"id": "test_user_id"}, "id": "id1"}],
        "next": "http://next-page",
    }
    # Page 2: Found
    page2 = {
        "items": [{"name": "Target", "owner": {"id": "test_user_id"}, "id": "target_id"}],
        "next": None,
    }
    mock_spotify.current_user_playlists.side_effect = [page1, page2]

    pid = builder.find_playlist_by_name("Target")
    assert pid == "target_id"
    assert mock_spotify.current_user_playlists.call_count == 2


def test_find_playlist_by_name_not_found(builder, mock_spotify):
    """Test behavior when playlist does not exist."""
    mock_spotify.current_user_playlists.return_value = {"items": [], "next": None}
    pid = builder.find_playlist_by_name("Nonexistent")
    assert pid is None


def test_get_playlist_tracks_pagination(builder, mock_spotify):
    """Test retrieving playlist tracks with pagination."""
    # Page 1: 100 tracks
    page1_items = [{"track": {"uri": f"spotify:track:{i}"}} for i in range(100)]
    page1 = {"items": page1_items, "next": "http://next"}

    # Page 2: 10 tracks
    page2_items = [{"track": {"uri": f"spotify:track:{i+100}"}} for i in range(10)]
    page2 = {"items": page2_items, "next": None}

    mock_spotify.playlist_tracks.side_effect = [page1, page2]

    tracks = builder.get_playlist_tracks("pid")
    assert len(tracks) == 110
    assert tracks[0] == "spotify:track:0"
    assert tracks[-1] == "spotify:track:109"


def test_clear_playlist(builder, mock_spotify):
    """Test clearing all tracks from a playlist."""
    # Mock getting 150 tracks
    with patch.object(builder, "get_playlist_tracks") as mock_get_tracks:
        mock_get_tracks.return_value = [f"spotify:track:{i}" for i in range(150)]

        builder.clear_playlist("pid")

        # Should remove in batches of 100
        assert mock_spotify.playlist_remove_all_occurrences_of_items.call_count == 2

        # Check first batch size
        args1, _ = mock_spotify.playlist_remove_all_occurrences_of_items.call_args_list[0]
        assert len(args1[1]) == 100

        # Check second batch size
        args2, _ = mock_spotify.playlist_remove_all_occurrences_of_items.call_args_list[1]
        assert len(args2[1]) == 50


def test_update_playlist_details(builder, mock_spotify):
    """Test updating playlist details when changes are needed."""
    # Current state: different description, different public status
    mock_spotify.playlist.return_value = {"description": "Old Description", "public": True}

    builder.update_playlist_details("pid", "New Description", public=False)

    mock_spotify.playlist_change_details.assert_called_with(
        "pid", description="New Description", public=False
    )


def test_update_playlist_details_no_change(builder, mock_spotify):
    """Test that no update call is made if details match."""
    mock_spotify.playlist.return_value = {"description": "Same Description", "public": False}

    builder.update_playlist_details("pid", "Same Description", public=False)

    mock_spotify.playlist_change_details.assert_not_called()


def test_get_playlist_tracks_details(builder, mock_spotify):
    """Test retrieving full track details."""
    mock_spotify.playlist_tracks.return_value = {
        "items": [
            {
                "track": {
                    "name": "Track 1",
                    "artists": [{"name": "Artist 1"}],
                    "album": {"name": "Album 1"},
                }
            },
            {
                "track": {
                    "name": "Track 2",
                    "artists": [{"name": "Artist 2"}],
                    "album": {"name": "Album 2"},
                }
            },
        ],
        "next": None,
    }

    details = builder.get_playlist_tracks_details("pid")

    assert len(details) == 2
    assert details[0] == {"artist": "Artist 1", "track": "Track 1", "album": "Album 1"}


def test_export_playlist_to_json(builder, mock_spotify):
    """Test exporting a playlist to a JSON file."""
    # Mock finding playlist
    with patch.object(builder, "find_playlist_by_name", return_value="pid"):
        # Mock playlist details
        mock_spotify.playlist.return_value = {"description": "Desc", "public": True}

        # Mock getting tracks
        with patch.object(
            builder, "get_playlist_tracks_details", return_value=[{"artist": "A", "track": "B"}]
        ):

            # Mock file I/O
            with patch("builtins.open", new_callable=MagicMock) as mock_open:
                builder.export_playlist_to_json("My Playlist", "out.json")

                # Verify file write
                mock_open.assert_called_with("out.json", "w")
                handle = mock_open.return_value.__enter__.return_value
                # We expect json.dump to write something
                assert handle.write.call_count > 0


def test_build_playlist_from_json_dry_run(builder, mock_spotify):
    """Test dry run mode does not create/update playlists."""
    playlist_data = {"name": "New Playlist", "tracks": [{"artist": "A", "track": "B"}]}

    with patch("json.load", return_value=playlist_data), patch("builtins.open", MagicMock()):

        with patch.object(builder, "search_track", return_value="uri:1"):
            builder.build_playlist_from_json("file.json", dry_run=True)

            # Should not check for existing playlist or create one
            mock_spotify.current_user_playlists.assert_not_called()
            mock_spotify.user_playlist_create.assert_not_called()


def test_build_playlist_from_json_create_new(builder, mock_spotify):
    """Test creating a new playlist from JSON."""
    playlist_data = {"name": "New Playlist", "tracks": [{"artist": "A", "track": "B"}]}

    with patch("json.load", return_value=playlist_data), patch("builtins.open", MagicMock()):

        # Mock: Playlist doesn't exist
        with (
            patch.object(builder, "find_playlist_by_name", return_value=None),
            patch.object(builder, "search_track", return_value="uri:1"),
            patch.object(builder, "create_playlist", return_value="new_pid") as mock_create,
            patch.object(builder, "_add_track_uris_to_playlist") as mock_add,
        ):

            builder.build_playlist_from_json("file.json")

            mock_create.assert_called()
            mock_add.assert_called_with("new_pid", ["uri:1"])


def test_build_playlist_from_json_update_existing(builder, mock_spotify):
    """Test updating an existing playlist from JSON."""
    playlist_data = {"name": "Existing Playlist", "tracks": [{"artist": "A", "track": "B"}]}

    with patch("json.load", return_value=playlist_data), patch("builtins.open", MagicMock()):

        # Mock: Playlist exists
        with (
            patch.object(builder, "find_playlist_by_name", return_value="existing_pid"),
            patch.object(builder, "search_track", return_value="uri:new"),
            patch.object(builder, "get_playlist_tracks", return_value=["uri:old"]),
            patch.object(builder, "update_playlist_details") as mock_update,
            patch.object(builder, "clear_playlist") as mock_clear,
            patch.object(builder, "_add_track_uris_to_playlist") as mock_add,
        ):

            builder.build_playlist_from_json("file.json")

            mock_update.assert_called()
            mock_clear.assert_called_with("existing_pid")
            mock_add.assert_called_with("existing_pid", ["uri:new"])


def test_similarity(builder):
    """Test the string similarity utility."""
    # Identical strings
    assert builder._similarity("test", "test") == 1.0
    # Case insensitive
    assert builder._similarity("TEST", "test") == 1.0
    # Completely different
    assert builder._similarity("abc", "xyz") == 0.0
    # Partial match
    assert builder._similarity("hello world", "hello") > 0.4


def test_backup_all_playlists(builder, mock_spotify):
    """Test backing up all playlists."""
    # Mock finding playlists
    mock_spotify.current_user_playlists.side_effect = [
        {
            "items": [
                {"name": "Playlist 1", "id": "p1"},
                {"name": "Playlist/2", "id": "p2"},  # Test filename sanitization
            ],
            "next": None,
        }
    ]

    with patch.object(builder, "export_playlist_to_json") as mock_export:
        builder.backup_all_playlists("backups_dir")

        assert mock_export.call_count == 2
        # Check filename sanitization (slashes removed/replaced)
        mock_export.assert_any_call("Playlist 1", os.path.join("backups_dir", "Playlist 1.json"))
        # Implementation strips special chars, check specific sanitization logic
        # 'Playlist/2' -> 'Playlist2' or similar depending on implementation
        # The implementation uses: "".join(c for c in name if c.isalnum()
        # or c in (" ", "-", "_")).strip()
        mock_export.assert_any_call("Playlist/2", os.path.join("backups_dir", "Playlist2.json"))


def test_get_credentials_from_keyring_success():
    """Test retrieving credentials from keyring."""
    with patch("spotify_playlist_builder.keyring") as mock_keyring:
        mock_keyring.get_password.side_effect = ["my_id", "my_secret"]

        cid, secret = get_credentials_from_keyring()

        assert cid == "my_id"
        assert secret == "my_secret"
        assert mock_keyring.get_password.call_count == 2


def test_get_credentials_from_keyring_missing():
    """Test error when credentials are missing in keyring."""
    with patch("spotify_playlist_builder.keyring") as mock_keyring:
        mock_keyring.get_password.return_value = None

        with pytest.raises(Exception) as exc:
            get_credentials_from_keyring()

        assert "Credentials not found in keychain" in str(exc.value)


def test_store_credentials_in_keyring():
    """Test storing credentials in keyring."""
    with patch("spotify_playlist_builder.keyring") as mock_keyring:
        store_credentials_in_keyring("new_id", "new_secret")

        mock_keyring.set_password.assert_any_call("spotify-playlist-builder", "client_id", "new_id")
        mock_keyring.set_password.assert_any_call(
            "spotify-playlist-builder", "client_secret", "new_secret"
        )


def test_get_credentials_dispatch():
    """Test that get_credentials calls the correct implementation."""
    with patch(
        "spotify_playlist_builder.get_credentials_from_env", return_value=("a", "b")
    ) as mock_env:
        assert get_credentials("env") == ("a", "b")
        mock_env.assert_called_once()

    with patch(
        "spotify_playlist_builder.get_credentials_from_keyring", return_value=("c", "d")
    ) as mock_keyring:
        assert get_credentials("keyring") == ("c", "d")
        mock_keyring.assert_called_once()


def test_get_builder():
    """Test the factory function creates a builder correctly."""
    with (
        patch("spotify_playlist_builder.get_credentials", return_value=("cid", "sec")),
        patch("spotify_playlist_builder.SpotifyPlaylistBuilder") as mock_cls,
    ):

        get_builder(CredentialSource.env)

        mock_cls.assert_called_with("cid", "sec")


# --- CLI Tests for 90%+ Coverage ---


def test_cli_build_success():
    """Test the build command."""
    with patch("spotify_playlist_builder.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_get_builder.return_value = mock_builder

        # Create a dummy file for the argument
        with runner.isolated_filesystem():
            with open("playlist.json", "w") as f:
                f.write("{}")

            result = runner.invoke(app, ["build", "playlist.json", "--source", "env"])

            assert result.exit_code == 0
            mock_builder.build_playlist_from_json.assert_called_once()


def test_cli_build_error():
    """Test the build command handling errors."""
    with patch("spotify_playlist_builder.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_builder.build_playlist_from_json.side_effect = Exception("Build failed")
        mock_get_builder.return_value = mock_builder

        with runner.isolated_filesystem():
            with open("playlist.json", "w") as f:
                f.write("{}")

            result = runner.invoke(app, ["build", "playlist.json"])

            assert result.exit_code == 1
            mock_builder.build_playlist_from_json.assert_called_once()


def test_cli_export_success():
    """Test the export command."""
    with patch("spotify_playlist_builder.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_get_builder.return_value = mock_builder

        result = runner.invoke(app, ["export", "My Playlist", "out.json"])

        assert result.exit_code == 0
        mock_builder.export_playlist_to_json.assert_called_with("My Playlist", "out.json")


def test_cli_backup_success():
    """Test the backup command."""
    with patch("spotify_playlist_builder.get_builder") as mock_get_builder:
        mock_builder = MagicMock()
        mock_get_builder.return_value = mock_builder

        result = runner.invoke(app, ["backup", "backups_dir"])

        assert result.exit_code == 0
        mock_builder.backup_all_playlists.assert_called_with("backups_dir")


def test_cli_store_credentials():
    """Test storing credentials interactively."""
    with patch("spotify_playlist_builder.store_credentials_in_keyring") as mock_store:
        # Simulate user input: client_id, then client_secret
        result = runner.invoke(app, ["store-credentials"], input="my_id\nmy_secret\n")

        assert result.exit_code == 0
        mock_store.assert_called_with("my_id", "my_secret")


def test_cli_store_credentials_missing_input():
    """Test error when input is missing."""
    result = runner.invoke(app, ["store-credentials"], input="\n\n")  # Empty inputs
    assert result.exit_code == 1


def test_cli_main_verbose():
    """Test global options like verbose."""
    # Just checking it doesn't crash and sets level
    with patch("logging.basicConfig"):
        result = runner.invoke(app, ["--verbose", "build", "--help"])
        assert result.exit_code == 0


def test_init_auth_failure():
    """Test initialization failing when Spotify user cannot be retrieved."""
    with (
        patch("spotify_playlist_builder.SpotifyOAuth"),
        patch("spotify_playlist_builder.spotipy.Spotify") as mock_spotify,
    ):

        # Mock auth returning None
        mock_spotify.return_value.current_user.return_value = None

        with pytest.raises(Exception) as exc:
            SpotifyPlaylistBuilder("id", "secret")

        assert "Failed to authenticate" in str(exc.value)


def test_keyring_dependency_missing():
    """Test error message when keyring module is not installed."""
    # Simulate keyring being None (ImportError fallback)
    with patch("spotify_playlist_builder.keyring", None):
        with pytest.raises(Exception) as exc:
            get_credentials_from_keyring()

        assert "keyring library not available" in str(exc.value)

        with pytest.raises(Exception) as exc:
            store_credentials_in_keyring("id", "secret")
        assert "keyring library not available" in str(exc.value)


def test_cli_install_completion_success():
    """Test successful installation of zsh completion."""
    with (
        patch("pathlib.Path.home") as mock_home,
        patch("subprocess.run") as mock_run,
        patch("builtins.open", new_callable=MagicMock) as mock_open,
    ):

        # Setup mocks
        mock_omz = MagicMock()
        mock_omz.exists.return_value = True
        # Path configuration: home / .oh-my-zsh
        mock_home.return_value.__truediv__.return_value = mock_omz
        # Mock completions dir: omz / completions
        mock_completions = MagicMock()
        mock_omz.__truediv__.return_value = mock_completions
        # Mock target file: completions / _script
        mock_target = MagicMock()
        mock_completions.__truediv__.return_value = mock_target

        # Mock subprocess result
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "completion script content"

        result = runner.invoke(app, ["install-zsh-completion"])

        assert result.exit_code == 0
        # Check if subprocess was called to generate script
        mock_run.assert_called_once()
        # Check if file was written
        mock_open.assert_called_with(mock_target, "w")
        mock_open.return_value.__enter__.return_value.write.assert_called_with(
            "completion script content"
        )


def test_cli_install_completion_no_omz():
    """Test installation fails if Oh My Zsh is not found."""
    with patch("pathlib.Path.home") as mock_home:
        mock_omz = MagicMock()
        mock_omz.exists.return_value = False
        mock_home.return_value.__truediv__.return_value = mock_omz

        result = runner.invoke(app, ["install-zsh-completion"])

        assert result.exit_code == 1


def test_cli_install_completion_subprocess_error():
    """Test installation fails if completion generation fails."""
    with patch("pathlib.Path.home") as mock_home, patch("subprocess.run") as mock_run:

        mock_omz = MagicMock()
        mock_omz.exists.return_value = True
        mock_home.return_value.__truediv__.return_value = mock_omz

        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error generating"

        result = runner.invoke(app, ["install-zsh-completion"])

        assert result.exit_code == 1


def test_cli_uninstall_completion():
    """Test uninstall instruction command."""
    result = runner.invoke(app, ["uninstall-completion"])
    assert result.exit_code == 0
