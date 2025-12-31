import pytest
from backend.app.core.auth.manager import UserManager
from backend.app.models.user import User
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.asyncio
async def test_user_manager_on_after_register():
    """Test the on_after_register hook in UserManager."""
    mock_user_db = MagicMock()
    # Mock update to allow await
    mock_user_db.update = AsyncMock()

    manager = UserManager(mock_user_db)
    user = User(id="123", email="test@example.com", is_superuser=False)

    # Patch send_email to avoid side effects
    with patch("backend.app.core.auth.manager.send_email", new_callable=AsyncMock):
        await manager.on_after_register(user)


@pytest.mark.asyncio
async def test_promote_admin_on_login():
    """Test that a user is promoted to admin if their email is in ADMIN_EMAILS."""
    mock_user_db = MagicMock()
    mock_user_db.update = AsyncMock()

    manager = UserManager(mock_user_db)
    user = User(id="123", email="admin@vibomat.com", is_superuser=False)

    with patch("os.getenv", return_value="admin@vibomat.com, other@vibomat.com"):
        await manager.on_after_login(user)

    mock_user_db.update.assert_called_once()
    call_args = mock_user_db.update.call_args
    assert call_args[0][0] == user
    assert call_args[0][1]["is_superuser"] is True
    assert call_args[0][1]["is_verified"] is True


@pytest.mark.asyncio
async def test_no_promote_if_not_admin_email():
    """Test that a user is NOT promoted if their email is not in ADMIN_EMAILS."""
    mock_user_db = MagicMock()
    mock_user_db.update = AsyncMock()

    manager = UserManager(mock_user_db)
    user = User(id="123", email="regular@vibomat.com", is_superuser=False)

    with patch("os.getenv", return_value="admin@vibomat.com"):
        await manager.on_after_login(user)

    mock_user_db.update.assert_not_called()


@pytest.mark.asyncio
async def test_no_promote_if_already_admin():
    """Test that no update happens if user is already admin."""
    mock_user_db = MagicMock()
    mock_user_db.update = AsyncMock()

    manager = UserManager(mock_user_db)
    user = User(id="123", email="admin@vibomat.com", is_superuser=True)

    with patch("os.getenv", return_value="admin@vibomat.com"):
        await manager.on_after_login(user)

    mock_user_db.update.assert_not_called()
