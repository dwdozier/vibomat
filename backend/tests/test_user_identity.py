import pytest
import uuid
from backend.app.models.user import User
from backend.app.core.auth.manager import UserManager
from fastapi_users.db import SQLAlchemyUserDatabase
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException


def get_mock_user_db():
    mock_user_db = MagicMock(spec=SQLAlchemyUserDatabase)
    mock_user_db.session = MagicMock()

    # Setup the chain: execute() -> result -> unique() -> scalar_one_or_none()
    mock_result = MagicMock()
    mock_unique = MagicMock()
    mock_result.unique.return_value = mock_unique
    mock_unique.scalar_one_or_none.return_value = None

    mock_user_db.session.execute = AsyncMock(return_value=mock_result)
    return mock_user_db, mock_result, mock_unique


@pytest.mark.asyncio
async def test_user_model_identity_fields():
    user = User(email="test@example.com", handle="vibemaster", first_name="Vibe", last_name="O'Mat")
    assert user.handle == "vibemaster"
    assert user.first_name == "Vibe"
    assert user.last_name == "O'Mat"


@pytest.mark.asyncio
async def test_user_manager_handle_validation():
    mock_user_db, _, _ = get_mock_user_db()
    manager = UserManager(mock_user_db)

    await manager.validate_handle("valid_handle")

    with pytest.raises(HTTPException) as exc:
        await manager.validate_handle("inv!")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_user_manager_handle_uniqueness():
    mock_user_db, _, mock_unique = get_mock_user_db()
    # Mock finding an existing user
    mock_unique.scalar_one_or_none.return_value = User(id=uuid.uuid4(), handle="taken")

    manager = UserManager(mock_user_db)

    with pytest.raises(HTTPException) as exc:
        await manager.validate_handle("taken")
    assert exc.value.status_code == 400

    # Test uniqueness check allowing same user to keep their handle
    user_id = uuid.uuid4()
    user = User(id=user_id, handle="my-handle")
    mock_unique.scalar_one_or_none.return_value = None

    await manager.validate_handle("my-handle", user=user)


def test_user_display_name_logic():
    u1 = User(email="a@b.com", handle="cooluser")
    assert u1.display_name == "cooluser"
    u2 = User(email="a@b.com", handle=None, first_name="John")
    assert u2.display_name == "John"
    u3 = User(email="bob@example.com", handle=None, first_name=None)
    assert u3.display_name == "bob@example.com"
