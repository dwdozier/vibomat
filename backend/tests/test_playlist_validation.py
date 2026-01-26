"""
Tests for playlist content validation schemas.

This module tests validation of playlist and track data to prevent malformed
data from entering the content_json field.
"""

import pytest
from pydantic import ValidationError

from backend.app.schemas.playlist import TrackContentSchema, PlaylistContentSchema
from backend.app.exceptions import InvalidPlaylistDataError


class TestTrackContentSchema:
    """Test track content validation."""

    def test_valid_track_minimal(self):
        """Verify minimal valid track passes validation."""
        track = TrackContentSchema(artist="Artist Name", track="Track Title")
        assert track.artist == "Artist Name"
        assert track.track == "Track Title"
        assert track.duration_ms is None
        assert track.provider is None

    def test_valid_track_complete(self):
        """Verify complete valid track passes validation."""
        track = TrackContentSchema(
            artist="Test Artist",
            track="Test Track",
            album="Test Album",
            duration_ms=180000,
            provider="spotify",
            provider_id="123abc",
        )
        assert track.artist == "Test Artist"
        assert track.track == "Test Track"
        assert track.album == "Test Album"
        assert track.duration_ms == 180000
        assert track.provider == "spotify"
        assert track.provider_id == "123abc"

    def test_artist_required(self):
        """Verify artist field is required."""
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(track="Track Title")
        assert "artist" in str(exc_info.value)

    def test_track_required(self):
        """Verify track field is required."""
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist="Artist Name")
        assert "track" in str(exc_info.value)

    def test_artist_empty_string_rejected(self):
        """Verify empty artist string is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist="", track="Track Title")
        assert "artist" in str(exc_info.value)

    def test_track_empty_string_rejected(self):
        """Verify empty track string is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist="Artist Name", track="")
        assert "track" in str(exc_info.value)

    def test_artist_too_long_rejected(self):
        """Verify artist name over 255 chars is rejected."""
        long_artist = "A" * 256
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist=long_artist, track="Track Title")
        assert "artist" in str(exc_info.value)

    def test_track_too_long_rejected(self):
        """Verify track name over 255 chars is rejected."""
        long_track = "T" * 256
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist="Artist Name", track=long_track)
        assert "track" in str(exc_info.value)

    def test_artist_max_length_accepted(self):
        """Verify artist name at 255 chars is accepted."""
        max_artist = "A" * 255
        track = TrackContentSchema(artist=max_artist, track="Track Title")
        assert len(track.artist) == 255

    def test_track_max_length_accepted(self):
        """Verify track name at 255 chars is accepted."""
        max_track = "T" * 255
        track = TrackContentSchema(artist="Artist Name", track=max_track)
        assert len(track.track) == 255

    def test_duration_ms_negative_rejected(self):
        """Verify negative duration is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist="Artist Name", track="Track Title", duration_ms=-1)
        assert "duration_ms" in str(exc_info.value)

    def test_duration_ms_zero_accepted(self):
        """Verify zero duration is accepted."""
        track = TrackContentSchema(artist="Artist Name", track="Track Title", duration_ms=0)
        assert track.duration_ms == 0

    def test_duration_ms_max_24_hours_accepted(self):
        """Verify max duration of 24 hours (86400000ms) is accepted."""
        track = TrackContentSchema(artist="Artist Name", track="Track Title", duration_ms=86400000)
        assert track.duration_ms == 86400000

    def test_duration_ms_over_24_hours_rejected(self):
        """Verify duration over 24 hours is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist="Artist Name", track="Track Title", duration_ms=86400001)
        assert "duration_ms" in str(exc_info.value)

    def test_provider_spotify_accepted(self):
        """Verify spotify provider is accepted."""
        track = TrackContentSchema(artist="Artist Name", track="Track Title", provider="spotify")
        assert track.provider == "spotify"

    def test_provider_discogs_accepted(self):
        """Verify discogs provider is accepted."""
        track = TrackContentSchema(artist="Artist Name", track="Track Title", provider="discogs")
        assert track.provider == "discogs"

    def test_provider_musicbrainz_accepted(self):
        """Verify musicbrainz provider is accepted."""
        track = TrackContentSchema(artist="Artist Name", track="Track Title", provider="musicbrainz")
        assert track.provider == "musicbrainz"

    def test_provider_invalid_rejected(self):
        """Verify invalid provider is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TrackContentSchema(artist="Artist Name", track="Track Title", provider="invalid_provider")
        assert "provider" in str(exc_info.value)

    def test_provider_case_insensitive(self):
        """Verify provider validation is case-insensitive."""
        track = TrackContentSchema(artist="Artist Name", track="Track Title", provider="SPOTIFY")
        assert track.provider == "spotify"  # Should be normalized to lowercase


class TestPlaylistContentSchema:
    """Test playlist content validation."""

    def test_valid_playlist_minimal(self):
        """Verify minimal valid playlist passes validation."""
        playlist = PlaylistContentSchema(name="Test Playlist", tracks=[])
        assert playlist.name == "Test Playlist"
        assert playlist.tracks == []

    def test_valid_playlist_with_tracks(self):
        """Verify playlist with tracks passes validation."""
        tracks = [
            {"artist": "Artist 1", "track": "Track 1"},
            {"artist": "Artist 2", "track": "Track 2"},
        ]
        playlist = PlaylistContentSchema(name="Test Playlist", tracks=tracks)  # type: ignore
        assert playlist.name == "Test Playlist"
        assert len(playlist.tracks) == 2
        assert playlist.tracks[0].artist == "Artist 1"

    def test_name_required(self):
        """Verify name field is required."""
        with pytest.raises(ValidationError) as exc_info:
            PlaylistContentSchema(tracks=[])
        assert "name" in str(exc_info.value)

    def test_name_empty_rejected(self):
        """Verify empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlaylistContentSchema(name="", tracks=[])
        assert "name" in str(exc_info.value)

    def test_tracks_required(self):
        """Verify tracks field is required."""
        with pytest.raises(ValidationError) as exc_info:
            PlaylistContentSchema(name="Test Playlist")
        assert "tracks" in str(exc_info.value)

    def test_max_tracks_10000_accepted(self):
        """Verify playlist with 10,000 tracks is accepted."""
        tracks = [{"artist": f"Artist {i}", "track": f"Track {i}"} for i in range(10000)]
        playlist = PlaylistContentSchema(name="Large Playlist", tracks=tracks)  # type: ignore
        assert len(playlist.tracks) == 10000

    def test_max_tracks_over_10000_rejected(self):
        """Verify playlist with over 10,000 tracks is rejected."""
        tracks = [{"artist": f"Artist {i}", "track": f"Track {i}"} for i in range(10001)]
        with pytest.raises(ValidationError) as exc_info:
            PlaylistContentSchema(name="Too Large Playlist", tracks=tracks)  # type: ignore
        assert "tracks" in str(exc_info.value)

    def test_invalid_track_rejected(self):
        """Verify playlist with invalid track is rejected."""
        tracks = [
            {"artist": "Valid Artist", "track": "Valid Track"},
            {"artist": "", "track": "Invalid Track"},  # Empty artist
        ]
        with pytest.raises(ValidationError) as exc_info:
            PlaylistContentSchema(name="Test Playlist", tracks=tracks)  # type: ignore
        assert "tracks" in str(exc_info.value)

    def test_track_with_invalid_duration_rejected(self):
        """Verify playlist with track having invalid duration is rejected."""
        tracks = [
            {
                "artist": "Artist Name",
                "track": "Track Title",
                "duration_ms": 99999999,  # Over 24 hours
            }
        ]
        with pytest.raises(ValidationError) as exc_info:
            PlaylistContentSchema(name="Test Playlist", tracks=tracks)  # type: ignore
        assert "duration_ms" in str(exc_info.value)


class TestInvalidPlaylistDataError:
    """Test InvalidPlaylistDataError exception."""

    def test_exception_created(self):
        """Verify InvalidPlaylistDataError can be raised."""
        with pytest.raises(InvalidPlaylistDataError) as exc_info:
            raise InvalidPlaylistDataError("Invalid playlist data")
        assert "Invalid playlist data" in str(exc_info.value)

    def test_exception_with_details(self):
        """Verify InvalidPlaylistDataError includes details."""
        error = InvalidPlaylistDataError("Invalid track data", details={"field": "artist", "value": ""})
        assert error.message == "Invalid track data"
        assert error.details == {"field": "artist", "value": ""}
        assert error.status_code == 400


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_artist_name(self):
        """Verify unicode characters in artist name are accepted."""
        track = TrackContentSchema(artist="Björk", track="Army of Me")
        assert track.artist == "Björk"

    def test_special_characters_in_track_name(self):
        """Verify special characters in artist and track names are accepted."""
        track = TrackContentSchema(artist="AC/DC", track="Rock 'N' Roll (Ain't Noise Pollution)")
        assert "/" in track.artist
        assert "'" in track.track
        assert "(" in track.track
        assert ")" in track.track

    def test_empty_tracks_list_accepted(self):
        """Verify empty tracks list is valid."""
        playlist = PlaylistContentSchema(name="Empty Playlist", tracks=[])
        assert len(playlist.tracks) == 0

    def test_whitespace_only_artist_rejected(self):
        """Verify whitespace-only artist is rejected."""
        with pytest.raises(ValidationError):
            TrackContentSchema(artist="   ", track="Track Title")

    def test_whitespace_only_track_rejected(self):
        """Verify whitespace-only track is rejected."""
        with pytest.raises(ValidationError):
            TrackContentSchema(artist="Artist Name", track="   ")

    def test_whitespace_trimmed(self):
        """Verify leading/trailing whitespace is trimmed."""
        track = TrackContentSchema(artist="  Artist Name  ", track="  Track Title  ")
        assert track.artist == "Artist Name"
        assert track.track == "Track Title"
