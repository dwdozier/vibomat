import os
import pytest
from unittest.mock import MagicMock, patch
from spotify_playlist_builder.auth import (
    get_credentials_from_env,
    get_credentials_from_keyring,
    store_credentials_in_keyring,
    get_credentials,
    CredentialSource,
)
from spotify_playlist_builder import get_builder, SpotifyPlaylistBuilder

# Credential Tests


def test_get_credentials_from_env_success():
    """Test retrieving credentials from environment variables."""
    env_vars = {"SPOTIFY_CLIENT_ID": "test_id", "SPOTIFY_CLIENT_SECRET": "test_secret"}
    with patch("dotenv.load_dotenv"), patch.dict(os.environ, env_vars):
        result = get_credentials_from_env()
        assert result is not None
        cid, secret = result
        assert cid == "test_id"
        assert secret == "test_secret"


def test_get_credentials_from_env_missing():
    """Test error when environment variables are missing."""
    with patch("dotenv.load_dotenv"), patch.dict(os.environ, {}, clear=True):
        with pytest.raises(Exception) as exc:
            get_credentials_from_env()
        assert "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not found" in str(exc.value)


def test_get_credentials_from_keyring_success():
    """Test retrieving credentials from keyring."""
    with patch("spotify_playlist_builder.auth.keyring") as mock_keyring:
        mock_keyring.get_password.side_effect = ["my_id", "my_secret"]

        result = get_credentials_from_keyring()
        assert result is not None
        cid, secret = result

        assert cid == "my_id"
        assert secret == "my_secret"
        assert mock_keyring.get_password.call_count == 2


def test_get_credentials_from_keyring_missing():
    """Test error when credentials are missing in keyring."""
    with patch("spotify_playlist_builder.auth.keyring") as mock_keyring:
        mock_keyring.get_password.return_value = None

        with pytest.raises(Exception) as exc:
            get_credentials_from_keyring()

        assert "Credentials not found in keychain" in str(exc.value)


def test_store_credentials_in_keyring():
    """Test storing credentials in keyring."""
    with patch("spotify_playlist_builder.auth.keyring") as mock_keyring:
        store_credentials_in_keyring("new_id", "new_secret")

        mock_keyring.set_password.assert_any_call("spotify-playlist-builder", "client_id", "new_id")
        mock_keyring.set_password.assert_any_call(
            "spotify-playlist-builder", "client_secret", "new_secret"
        )


def test_get_credentials_dispatch():
    """Test that get_credentials calls the correct implementation."""
    with patch(
        "spotify_playlist_builder.auth.get_credentials_from_env", return_value=("a", "b")
    ) as mock_env:
        assert get_credentials("env") == ("a", "b")
        mock_env.assert_called_once()

    with patch(
        "spotify_playlist_builder.auth.get_credentials_from_keyring", return_value=("c", "d")
    ) as mock_keyring:
        assert get_credentials("keyring") == ("c", "d")
        mock_keyring.assert_called_once()


def test_get_credentials_invalid_source():
    """Test error for unknown credential source."""
    with pytest.raises(ValueError) as exc:
        get_credentials("invalid")
    assert "Unknown credential source" in str(exc.value)


def test_get_builder():
    """Test the factory function creates a builder correctly."""
    with (
        patch("spotify_playlist_builder.auth.get_credentials", return_value=("cid", "sec")),
        patch("spotify_playlist_builder.client.SpotifyPlaylistBuilder") as mock_cls,
    ):
        get_builder(CredentialSource.env)
        mock_cls.assert_called_once()


def test_keyring_dependency_missing():
    """Test error message when keyring module is not installed."""
    # Simulate keyring being None (ImportError fallback)
    with patch("spotify_playlist_builder.auth.keyring", None):
        with pytest.raises(Exception) as exc:
            get_credentials_from_keyring()
        assert "keyring library not available" in str(exc.value)

        with pytest.raises(Exception) as exc:
            store_credentials_in_keyring("id", "secret")
        assert "keyring library not available" in str(exc.value)


# Core Logic Tests


def test_init_auth_failure():
    """Test initialization failing when Spotify user cannot be retrieved."""
    with (
        patch("spotify_playlist_builder.client.SpotifyOAuth"),
        patch("spotify_playlist_builder.client.spotipy.Spotify") as mock_spotify,
    ):
        # Mock auth returning None
        mock_spotify.return_value.current_user.return_value = None
        with pytest.raises(Exception) as exc:
            SpotifyPlaylistBuilder("id", "secret")
        assert "Failed to authenticate" in str(exc.value)


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


def test_search_track_limit_1_strategy_success(builder, mock_spotify):
    """Test exact match strategy when album is provided."""
    # Mock first search (specific album) returning a hit
    mock_spotify.search.side_effect = [
        {
            "tracks": {
                "items": [
                    {
                        "name": "Song",
                        "artists": [{"name": "Artist"}],
                        "album": {"name": "Album"},
                        "uri": "spotify:track:specific",
                    }
                ]
            }
        }
    ]
    uri = builder.search_track("Artist", "Song", "Album")
    assert uri == "spotify:track:specific"
    # Ensure limit=1 was used
    args, kwargs = mock_spotify.search.call_args
    assert kwargs["limit"] == 1


def test_search_track_limit_1_strategy_failure(builder, mock_spotify):
    """Test exact match strategy failing and falling back."""
    # Mock first search (specific album) failing, second (fallback) succeeding
    mock_spotify.search.side_effect = [
        {"tracks": {"items": []}},  # Specific search fails
        {
            "tracks": {
                "items": [
                    {
                        "name": "Song",
                        "artists": [{"name": "Artist"}],
                        "album": {"name": "Album"},
                        "uri": "spotify:track:fallback",
                    }
                ]
            }
        },
    ]
    uri = builder.search_track("Artist", "Song", "Album")
    assert uri == "spotify:track:fallback"
    # Verify both calls
    assert mock_spotify.search.call_count == 2


def test_search_track_fallback_failure(builder, mock_spotify):
    """Test fallback search returning no results."""
    mock_spotify.search.return_value = {"tracks": {"items": []}}
    uri = builder.search_track("Artist", "Song")
    assert uri is None


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


def test_get_playlist_tracks_break(builder, mock_spotify):
    """Test break condition in get_playlist_tracks."""
    # Single page
    mock_spotify.playlist_tracks.return_value = {"items": [], "next": None}
    builder.get_playlist_tracks("pid")


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


def test_clear_playlist_empty(builder, mock_spotify):
    """Test clearing a playlist that is already empty."""
    with patch.object(builder, "get_playlist_tracks", return_value=[]):
        builder.clear_playlist("pid")
        mock_spotify.playlist_remove_all_occurrences_of_items.assert_not_called()


def test_create_playlist(builder, mock_spotify):
    """Test playlist creation parameters."""
    mock_spotify.user_playlist_create.return_value = {"id": "new_pid"}
    pid = builder.create_playlist("My List", "Description", public=False)
    assert pid == "new_pid"
    mock_spotify.user_playlist_create.assert_called_with(
        user="test_user_id", name="My List", public=False, description="Description"
    )


def test_create_playlist_failure(builder, mock_spotify):
    """Test exception when playlist creation fails."""
    mock_spotify.user_playlist_create.return_value = None
    with pytest.raises(Exception) as exc:
        builder.create_playlist("Name")
    assert "Failed to create playlist" in str(exc.value)


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


def test_add_tracks_to_playlist_batching(builder, mock_spotify):
    """Test that tracks are added in batches of 100."""
    with patch.object(builder, "search_track", return_value="spotify:track:1"):
        # Create 105 dummy tracks
        tracks = [{"artist": "A", "track": "B"}] * 105
        builder.add_tracks_to_playlist("pid", tracks)

        # Should be called twice: once for 100 tracks, once for 5 tracks
        assert mock_spotify.playlist_add_items.call_count == 2


def test_add_tracks_to_playlist_failures(builder, mock_spotify):
    """Test adding tracks where some are not found."""
    # Mock search_track to find first, fail second
    with patch.object(builder, "search_track", side_effect=["uri:1", None]):
        tracks = [{"artist": "A", "track": "Found"}, {"artist": "B", "track": "Missing"}]
        failed = builder.add_tracks_to_playlist("pid", tracks)

        assert len(failed) == 1
        assert failed[0] == "B - Missing"
        # Verify only one track was added
        mock_spotify.playlist_add_items.assert_called_with("pid", ["uri:1"])


def test_add_tracks_all_missing(builder, mock_spotify):
    """Test adding tracks where none are found."""
    with patch.object(builder, "search_track", return_value=None):
        tracks = [{"artist": "A", "track": "B"}]
        builder.add_tracks_to_playlist("pid", tracks)
        mock_spotify.playlist_add_items.assert_not_called()


def test_add_track_uris_empty(builder, mock_spotify):
    """Test adding an empty list of URIs."""
    builder._add_track_uris_to_playlist("pid", [])
    mock_spotify.playlist_add_items.assert_not_called()


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
    assert details[0]["artist"] == "Artist 1"
    assert "version" in details[0]


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


def test_export_playlist_not_found(builder, mock_spotify):
    """Test export fails if playlist doesn't exist."""
    with patch.object(builder, "find_playlist_by_name", return_value=None):
        with pytest.raises(Exception) as exc:
            builder.export_playlist_to_json("Ghost Playlist", "out.json")
        assert "Playlist 'Ghost Playlist' not found." in str(exc.value)


def test_export_playlist_details_failure(builder, mock_spotify):
    """Test export fails if playlist details cannot be fetched."""
    with patch.object(builder, "find_playlist_by_name", return_value="pid"):
        mock_spotify.playlist.return_value = None
        with pytest.raises(Exception) as exc:
            builder.export_playlist_to_json("Playlist", "out.json")
        assert "Failed to fetch details" in str(exc.value)


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
        mock_export.assert_any_call("Playlist 1", os.path.join("backups_dir", "playlist_1.json"))
        mock_export.assert_any_call("Playlist/2", os.path.join("backups_dir", "playlist_2.json"))


def test_backup_all_playlists_exception(builder, mock_spotify):
    """Test that one failed backup doesn't stop the whole process."""
    mock_spotify.current_user_playlists.return_value = {
        "items": [
            {"name": "Good Playlist", "id": "p1"},
            {"name": "Bad Playlist", "id": "p2"},
        ],
        "next": None,
    }
    # First export succeeds, second fails
    with patch.object(builder, "export_playlist_to_json", side_effect=[None, Exception("Boom")]):
        builder.backup_all_playlists("backups")
        # Should not raise exception


def test_build_playlist_from_json_dry_run(builder, mock_spotify):
    """Test dry run mode does not create/update playlists."""
    playlist_data = {"name": "New Playlist", "tracks": [{"artist": "A", "track": "B"}]}
    with patch("json.load", return_value=playlist_data), patch("builtins.open", MagicMock()):
        with patch.object(builder, "search_track", return_value="uri:1"):
            builder.build_playlist_from_json("file.json", dry_run=True)
            # Should not check for existing playlist or create one
            mock_spotify.current_user_playlists.assert_not_called()
            mock_spotify.user_playlist_create.assert_not_called()


def test_build_dry_run_with_failures(builder, mock_spotify):
    """Test dry run mode reporting missing tracks."""
    playlist_data = {"name": "New Playlist", "tracks": [{"artist": "A", "track": "B"}]}
    with patch("json.load", return_value=playlist_data), patch("builtins.open", MagicMock()):
        with patch.object(builder, "search_track", return_value=None):  # Fail search
            builder.build_playlist_from_json("file.json", dry_run=True)


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


def test_search_track_version_preference_live(builder, mock_spotify):
    """Test preferring live version."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song (Studio)",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:studio",
                },
                {
                    "name": "Song (Live)",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Live at Venue"},
                    "uri": "spotify:track:live",
                },
            ]
        }
    }

    # Expect live version
    uri = builder.search_track("Artist", "Song", version="live")
    assert uri == "spotify:track:live"


def test_search_track_version_preference_studio(builder, mock_spotify):
    """Test preferring studio version (default)."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song (Live)",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Live at Venue"},
                    "uri": "spotify:track:live",
                },
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:studio",
                },
            ]
        }
    }

    # Expect studio version
    uri = builder.search_track("Artist", "Song", version="studio")
    assert uri == "spotify:track:studio"


def test_search_track_version_preference_remix(builder, mock_spotify):
    """Test preferring remix version."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:studio",
                },
                {
                    "name": "Song (Remix)",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:remix",
                },
            ]
        }
    }

    # Expect remix version
    uri = builder.search_track("Artist", "Song", version="remix")
    assert uri == "spotify:track:remix"


def test_determine_version(builder):
    """Test the version determination logic."""
    assert builder._determine_version("Track (Live)", "Album") == "live"
    assert builder._determine_version("Track", "Live at Venue") == "live"
    assert builder._determine_version("Track (Remix)", "Album") == "remix"
    assert builder._determine_version("Track (Mix)", "Album") == "remix"
    assert builder._determine_version("Track", "Greatest Hits") == "compilation"
    assert builder._determine_version("Track (Remastered)", "Album") == "remaster"
    assert builder._determine_version("Track", "Album (Remaster)") == "remaster"
    assert builder._determine_version("Track", "Album") == "studio"


def test_search_track_version_preference_original(builder, mock_spotify):
    """Test preferring original version over remaster."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song (Remastered)",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:remaster",
                },
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:original",
                },
            ]
        }
    }

    uri = builder.search_track("Artist", "Song", version="original")
    assert uri == "spotify:track:original"


def test_search_track_version_preference_remaster(builder, mock_spotify):
    """Test preferring remaster version over original."""
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:original",
                },
                {
                    "name": "Song (Remastered)",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Album"},
                    "uri": "spotify:track:remaster",
                },
            ]
        }
    }

    uri = builder.search_track("Artist", "Song", version="remaster")
    assert uri == "spotify:track:remaster"


def test_search_track_with_external_verification(builder, mock_spotify):
    """Test that external verification boosts the score."""
    # Mock Spotify search returning two similar items
    mock_spotify.search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Song (Live)",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Live Album"},
                    "uri": "spotify:track:verified_live",
                },
                {
                    "name": "Song",
                    "artists": [{"name": "Artist"}],
                    "album": {"name": "Another Album"},
                    "uri": "spotify:track:unverified",
                },
            ]
        }
    }

    # Configure mock verifier to confirm the first track IS live
    # It receives (artist, track_name, version)
    def side_effect(artist, track, version):
        return "Live" in track  # Simulate verifying based on name for this test

    builder.metadata_verifier.verify_track_version.side_effect = side_effect

    # Search with "live" preference
    uri = builder.search_track("Artist", "Song", version="live")

    # Should pick the one verified by metadata (and internal logic)
    assert uri == "spotify:track:verified_live"
    # Ensure verification was called
    assert builder.metadata_verifier.verify_track_version.call_count >= 1


def test_get_credentials_auto_discovery_keyring(builder):
    """Test auto-discovery finding credentials in keyring."""
    with patch(
        "spotify_playlist_builder.auth.get_credentials_from_keyring", return_value=("id", "secret")
    ):
        result = get_credentials(None)
        assert result is not None
        cid, secret = result
        assert cid == "id"
        assert secret == "secret"


def test_get_credentials_auto_discovery_env(builder):
    """Test auto-discovery falling back to env when keyring fails."""
    with (
        patch("spotify_playlist_builder.auth.get_credentials_from_keyring", return_value=None),
        patch(
            "spotify_playlist_builder.auth.get_credentials_from_env", return_value=("id", "secret")
        ),
    ):
        result = get_credentials(None)
        assert result is not None
        cid, secret = result
        assert cid == "id"
        assert secret == "secret"


def test_get_credentials_auto_discovery_failure(builder):
    """Test auto-discovery failing when both sources are missing."""
    with (
        patch("spotify_playlist_builder.auth.get_credentials_from_keyring", return_value=None),
        patch("spotify_playlist_builder.auth.get_credentials_from_env", return_value=None),
    ):
        with pytest.raises(Exception) as exc:
            get_credentials(None)
        assert "Credentials not found" in str(exc.value)


def test_to_snake_case():
    """Test the snake_case conversion utility."""
    from spotify_playlist_builder.utils.helpers import to_snake_case

    assert to_snake_case("My Awesome Playlist") == "my_awesome_playlist"
    assert to_snake_case("Playlist-with-Dashes") == "playlist_with_dashes"
    assert to_snake_case("  Spaces and Symbols! @# ") == "spaces_and_symbols"
    assert to_snake_case("Multiple___Underscores") == "multiple_underscores"
