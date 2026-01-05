import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.models.playlist import Playlist
from sqlalchemy import select, text


@pytest.mark.asyncio
async def test_jsonb_deep_query(db_session: AsyncSession):
    """Test querying deep into JSONB data."""
    user = User(email="jsonb@example.com", hashed_password="h")
    db_session.add(user)
    await db_session.flush()

    # Create a playlist with rich nested data
    content = {
        "tracks": [
            {"artist": "The Midnight", "title": "Sunset", "genre": "Synthwave"},
            {"artist": "Gunship", "title": "Tech Noir", "genre": "Synthwave"},
            {"artist": "Daft Punk", "title": "One More Time", "genre": "House"},
        ],
        "metadata": {"mood": "nostalgic", "source_version": "2.0"},
    }

    playlist = Playlist(user_id=user.id, name="Deep Query Test", content_json=content)
    db_session.add(playlist)
    await db_session.commit()

    # Query using raw PostgreSQL JSONB operators to ensure they work
    # #>> operator for path to text
    stmt = select(Playlist).where(text("content_json #>> '{metadata,mood}' = 'nostalgic'"))
    result = await db_session.execute(stmt)
    db_pl = result.scalar_one()
    assert db_pl.name == "Deep Query Test"

    # Query for specific track within the array using containment @>
    # Note: containment operator @> requires JSONB on both sides
    stmt = select(Playlist).where(
        text('content_json::jsonb @> \'{"tracks": [{"artist": "Gunship"}]}\'::jsonb')
    )
    result = await db_session.execute(stmt)
    db_pl = result.scalar_one()
    assert db_pl.name == "Deep Query Test"
