import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.models.playlist import Playlist
from sqlalchemy import select, text, func


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
    stmt = select(Playlist).where(text('content_json::jsonb @> \'{"tracks": [{"artist": "Gunship"}]}\'::jsonb'))
    result = await db_session.execute(stmt)
    db_pl = result.scalar_one()
    assert db_pl.name == "Deep Query Test"


@pytest.mark.asyncio
async def test_full_text_search(db_session: AsyncSession):
    """Test full-text search on Artist and Track names."""
    from backend.app.models.metadata import Artist

    artists = [
        Artist(name="The Midnight"),
        Artist(name="Midnight City"),
        Artist(name="After Midnight"),
    ]
    db_session.add_all(artists)
    await db_session.flush()

    # Create a basic FTS query using plainto_tsquery
    stmt = select(Artist).where(
        func.to_tsvector("english", Artist.name).bool_op("@@")(func.plainto_tsquery("english", "midnight"))
    )
    result = await db_session.execute(stmt)
    results = result.scalars().all()
    assert len(results) >= 3


@pytest.mark.asyncio
async def test_fuzzy_search_trigram(db_session: AsyncSession):
    """Test fuzzy search using pg_trgm similarity."""
    from backend.app.models.metadata import Artist

    # Ensure pg_trgm is available
    await db_session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    artist = Artist(name="Daft Punk")
    db_session.add(artist)
    await db_session.flush()

    # Search with a typo using raw SQL to be sure about the operator/function
    stmt = select(Artist).where(text("similarity(name, 'Daft Punc') > 0.3"))
    result = await db_session.execute(stmt)
    db_artist = result.scalar_one()
    assert db_artist.name == "Daft Punk"


@pytest.mark.asyncio
async def test_vector_similarity_search(db_session: AsyncSession):
    """Test vector similarity search using pgvector."""
    from backend.app.models.ai_log import AIInteractionEmbedding
    from backend.app.models.user import User

    user = User(email="vector@example.com", hashed_password="h")
    db_session.add(user)
    await db_session.flush()

    # Create dummy embeddings (768 dimensions)
    # v1 is very different from target_v
    # v3 is very similar to target_v
    v1 = [0.1] * 768
    v2 = [0.5] * 768
    v3 = [0.9] * 768

    interactions = [
        AIInteractionEmbedding(user_id=user.id, prompt="Low vector", embedding=v1),
        AIInteractionEmbedding(user_id=user.id, prompt="Mid vector", embedding=v2),
        AIInteractionEmbedding(user_id=user.id, prompt="High vector", embedding=v3),
    ]
    db_session.add_all(interactions)
    await db_session.commit()

    # Search for nearest neighbor to a vector close to v3
    target_v = [0.85] * 768

    # We'll use Euclidean distance <-> for this test as it's more predictable
    # with these dummy vectors
    stmt = select(AIInteractionEmbedding).order_by(AIInteractionEmbedding.embedding.l2_distance(target_v)).limit(1)
    result = await db_session.execute(stmt)
    nearest = result.scalar_one()
    assert nearest.prompt == "High vector"
