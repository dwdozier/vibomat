import pytest
import uuid
import httpx
from sqlalchemy import select
from backend.app.models.user import User, user_favorite_playlists
from backend.app.models.playlist import Playlist
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.main import app


@pytest.mark.asyncio
async def test_public_profile_logic(db_session):
    """Test public vs private profile visibility."""
    user_id = uuid.uuid4()
    # Create a public user
    user = User(
        id=user_id,
        email="public@example.com",
        hashed_password="...",
        is_active=True,
        is_verified=True,
        is_public=True,
        favorite_artists=["Artist A"],
        unskippable_albums=[{"name": "Album 1", "artist": "Artist A"}],
    )
    db_session.add(user)

    # Create a private user
    private_user_id = uuid.uuid4()
    private_user = User(
        id=private_user_id,
        email="private@example.com",
        hashed_password="...",
        is_active=True,
        is_verified=True,
        is_public=False,
    )
    db_session.add(private_user)
    await db_session.commit()

    # Test GET public profile
    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(f"/api/v1/profile/{user_id}")
        assert response.status_code == 200
        assert response.json()["favorite_artists"] == ["Artist A"]

        # Test GET private profile (should be 404)
        response = await ac.get(f"/api/v1/profile/{private_user_id}")
        assert response.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_favoriting_logic(db_session):
    """Test favoriting and unfavoriting playlists."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id, email="fav@example.com", hashed_password="...", is_active=True, is_verified=True
    )
    db_session.add(user)

    owner_id = uuid.uuid4()
    owner = User(
        id=owner_id,
        email="owner@example.com",
        hashed_password="...",
        is_active=True,
        is_verified=True,
    )
    db_session.add(owner)

    playlist_id = uuid.uuid4()
    playlist = Playlist(
        id=playlist_id,
        user_id=owner_id,
        name="Public Jam",
        public=True,
        content_json={"tracks": []},
    )
    db_session.add(playlist)
    await db_session.commit()

    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session
    app.dependency_overrides[current_active_user] = lambda: user

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Favorite
        response = await ac.post(f"/api/v1/profile/playlists/{playlist_id}/favorite")
        assert response.status_code == 200

        # Check DB
        result = await db_session.execute(
            select(user_favorite_playlists).where(user_favorite_playlists.c.user_id == user_id)
        )
        assert result.scalar_one_or_none() is not None

        # Unfavorite
        response = await ac.delete(f"/api/v1/profile/playlists/{playlist_id}/favorite")
        assert response.status_code == 200

        result = await db_session.execute(
            select(user_favorite_playlists).where(user_favorite_playlists.c.user_id == user_id)
        )
        assert result.scalar_one_or_none() is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_public_playlists(db_session):
    """Test fetching public playlists."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="list@example.com",
        hashed_password="...",
        is_active=True,
        is_verified=True,
        is_public=True,
    )
    db_session.add(user)

    playlist = Playlist(
        id=uuid.uuid4(), user_id=user_id, name="Public", public=True, content_json={}
    )
    private_playlist = Playlist(
        id=uuid.uuid4(), user_id=user_id, name="Private", public=False, content_json={}
    )
    db_session.add_all([playlist, private_playlist])
    await db_session.commit()

    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(f"/api/v1/profile/{user_id}/playlists")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Public"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_favorite_edge_cases(db_session):
    """Test error handling in favoriting."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="edge@example.com",
        hashed_password="...",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    from backend.app.db.session import get_async_session

    app.dependency_overrides[get_async_session] = lambda: db_session
    app.dependency_overrides[current_active_user] = lambda: user

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Test favoriting non-existent playlist
        response = await ac.post(f"/api/v1/profile/playlists/{uuid.uuid4()}/favorite")
        assert response.status_code == 404

        # Test favoriting private playlist
        owner_id = uuid.uuid4()
        owner = User(
            id=owner_id,
            email="owner_edge@example.com",
            hashed_password="...",
            is_active=True,
            is_verified=True,
        )
        db_session.add(owner)
        private_playlist = Playlist(
            id=uuid.uuid4(), user_id=owner_id, name="Private", public=False, content_json={}
        )
        db_session.add(private_playlist)
        await db_session.commit()
        response = await ac.post(f"/api/v1/profile/playlists/{private_playlist.id}/favorite")
        assert response.status_code == 404

    app.dependency_overrides.clear()
