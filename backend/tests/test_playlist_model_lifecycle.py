import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.models.playlist import Playlist


@pytest.mark.asyncio
async def test_playlist_soft_delete_column(db_session: AsyncSession):
    """Test that we can set and retrieve the deleted_at column."""
    user = User(email="lifecycle@example.com", hashed_password="h")
    db_session.add(user)
    await db_session.flush()

    now = datetime.now(timezone.utc)

    # This should fail if deleted_at is not defined on the model
    try:
        playlist = Playlist(
            user_id=user.id, name="Lifecycle Playlist", content_json={"tracks": []}, deleted_at=now
        )
        db_session.add(playlist)
        await db_session.commit()
        await db_session.refresh(playlist)

        assert playlist.deleted_at is not None
        assert playlist.deleted_at == now
    except TypeError as e:
        # If the model doesn't accept the kwarg, it raises TypeError
        pytest.fail(f"Playlist model does not accept 'deleted_at': {e}")
    except Exception as e:
        # Other DB errors
        pytest.fail(f"Failed to save playlist with deleted_at: {e}")
