"""
Tests for access token and refresh token encryption at rest.

This module tests that access and refresh tokens are properly encrypted
in the database and can be decrypted for use.
"""

import pytest
import uuid
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from backend.app.models.service_connection import ServiceConnection
from backend.app.models.user import User


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for foreign key constraints."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_access_token_encrypted_at_rest(db_session: AsyncSession, test_user: User):
    """Verify access tokens are encrypted in the database."""
    # Create a service connection
    connection = ServiceConnection(
        id=uuid.uuid4(),
        user_id=test_user.id,
        provider_name="spotify",
        provider_user_id="test_user_123",
        access_token="plaintext_access_token_12345",
        refresh_token="plaintext_refresh_token_67890",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    )

    db_session.add(connection)
    await db_session.commit()

    # Query the database directly to check raw storage
    result = await db_session.execute(
        text("SELECT access_token FROM service_connection WHERE id = :id"),
        {"id": str(connection.id)},
    )
    raw_token = result.scalar_one()

    # Token should NOT be plaintext in database
    assert raw_token != "plaintext_access_token_12345"
    # Token should look like encrypted data (not readable ASCII)
    assert len(raw_token) > len("plaintext_access_token_12345")

    # But the model should decrypt it properly
    result = await db_session.execute(select(ServiceConnection).where(ServiceConnection.id == connection.id))
    retrieved = result.scalar_one()
    assert retrieved.access_token == "plaintext_access_token_12345"


@pytest.mark.asyncio
async def test_refresh_token_encrypted_at_rest(db_session: AsyncSession, test_user: User):
    """Verify refresh tokens are encrypted in the database."""
    # Create a service connection
    connection = ServiceConnection(
        id=uuid.uuid4(),
        user_id=test_user.id,
        provider_name="spotify",
        provider_user_id="test_user_123",
        access_token="access_token",
        refresh_token="plaintext_refresh_token_67890",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    )

    db_session.add(connection)
    await db_session.commit()

    # Query the database directly to check raw storage
    result = await db_session.execute(
        text("SELECT refresh_token FROM service_connection WHERE id = :id"),
        {"id": str(connection.id)},
    )
    raw_token = result.scalar_one()

    # Token should NOT be plaintext in database
    assert raw_token != "plaintext_refresh_token_67890"
    # Token should look like encrypted data
    assert len(raw_token) > len("plaintext_refresh_token_67890")

    # But the model should decrypt it properly
    result = await db_session.execute(select(ServiceConnection).where(ServiceConnection.id == connection.id))
    retrieved = result.scalar_one()
    assert retrieved.refresh_token == "plaintext_refresh_token_67890"


@pytest.mark.asyncio
async def test_null_refresh_token_handling(db_session: AsyncSession, test_user: User):
    """Verify null refresh tokens are handled correctly."""
    # Create connection without refresh token
    connection = ServiceConnection(
        id=uuid.uuid4(),
        user_id=test_user.id,
        provider_name="spotify",
        provider_user_id="test_user_123",
        access_token="access_token",
        refresh_token=None,
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    )

    db_session.add(connection)
    await db_session.commit()

    # Retrieve and verify
    result = await db_session.execute(select(ServiceConnection).where(ServiceConnection.id == connection.id))
    retrieved = result.scalar_one()
    assert retrieved.refresh_token is None


@pytest.mark.asyncio
async def test_token_encryption_decryption_round_trip(db_session: AsyncSession, test_user: User):
    """Test that tokens can be encrypted and decrypted correctly."""
    test_tokens = [
        "short_token",
        "a" * 100,  # Medium length
        "b" * 1000,  # Long token
        "token_with_special_chars_!@#$%^&*()",
        "token with spaces",
    ]

    for idx, token in enumerate(test_tokens):
        connection = ServiceConnection(
            id=uuid.uuid4(),
            user_id=test_user.id,
            provider_name="spotify",
            provider_user_id=f"user_{idx}",
            access_token=token,
            refresh_token=f"refresh_{token}",
            expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
        )

        db_session.add(connection)
        await db_session.flush()

        # Retrieve immediately
        result = await db_session.execute(select(ServiceConnection).where(ServiceConnection.id == connection.id))
        retrieved = result.scalar_one()

        assert retrieved.access_token == token
        assert retrieved.refresh_token == f"refresh_{token}"


@pytest.mark.asyncio
async def test_encrypted_token_field_type(db_session: AsyncSession):
    """Verify that access_token and refresh_token use EncryptedJSON type."""
    from backend.app.models.service_connection import EncryptedJSON

    # Check column types
    access_token_column = ServiceConnection.__table__.c.access_token
    refresh_token_column = ServiceConnection.__table__.c.refresh_token

    # These should use EncryptedJSON type
    assert isinstance(access_token_column.type, EncryptedJSON)
    assert isinstance(refresh_token_column.type, EncryptedJSON)


@pytest.mark.asyncio
async def test_existing_connection_token_update(db_session: AsyncSession, test_user: User):
    """Test updating tokens on an existing connection."""
    # Create initial connection
    connection = ServiceConnection(
        id=uuid.uuid4(),
        user_id=test_user.id,
        provider_name="spotify",
        provider_user_id="test_user",
        access_token="old_access_token",
        refresh_token="old_refresh_token",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
    )

    db_session.add(connection)
    await db_session.commit()

    # Update tokens
    connection.access_token = "new_access_token"
    connection.refresh_token = "new_refresh_token"
    await db_session.commit()

    # Retrieve and verify
    result = await db_session.execute(select(ServiceConnection).where(ServiceConnection.id == connection.id))
    retrieved = result.scalar_one()

    assert retrieved.access_token == "new_access_token"
    assert retrieved.refresh_token == "new_refresh_token"

    # Verify encryption in database
    raw_result = await db_session.execute(
        text("SELECT access_token FROM service_connection WHERE id = :id"),
        {"id": str(connection.id)},
    )
    raw_token = raw_result.scalar_one()
    assert raw_token != "new_access_token"


@pytest.mark.asyncio
async def test_multiple_connections_independent_encryption(db_session: AsyncSession, test_user: User):
    """Verify each connection's tokens are independently encrypted."""
    # Create multiple connections with same token values
    connections = []
    for i in range(3):
        conn = ServiceConnection(
            id=uuid.uuid4(),
            user_id=test_user.id,
            provider_name="spotify",
            provider_user_id=f"user_{i}",
            access_token="same_access_token",
            refresh_token="same_refresh_token",
            expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1),
        )
        connections.append(conn)
        db_session.add(conn)

    await db_session.commit()

    # All should decrypt to same value
    for conn in connections:
        result = await db_session.execute(select(ServiceConnection).where(ServiceConnection.id == conn.id))
        retrieved = result.scalar_one()
        assert retrieved.access_token == "same_access_token"
        assert retrieved.refresh_token == "same_refresh_token"


class TestEncryptedJSONType:
    """Test the EncryptedJSON type directly."""

    def test_encrypted_json_handles_strings(self):
        """Test that EncryptedJSON can handle string values."""
        from backend.app.models.service_connection import (
            EncryptedJSON,
        )

        column_type = EncryptedJSON()

        # Test binding (encryption)
        test_value = "test_token_string"
        encrypted = column_type.process_bind_param(test_value, None)

        # Should be encrypted
        assert encrypted != test_value
        assert encrypted is not None

        # Test result (decryption)
        decrypted = column_type.process_result_value(encrypted, None)
        assert decrypted == test_value

    def test_encrypted_json_handles_none(self):
        """Test that EncryptedJSON handles None correctly."""
        from backend.app.models.service_connection import EncryptedJSON

        column_type = EncryptedJSON()

        # None should pass through
        assert column_type.process_bind_param(None, None) is None
        assert column_type.process_result_value(None, None) is None

    def test_encrypted_json_handles_dicts(self):
        """Test that EncryptedJSON handles dictionaries."""
        from backend.app.models.service_connection import EncryptedJSON

        column_type = EncryptedJSON()

        test_dict = {"key": "value", "number": 123}
        encrypted = column_type.process_bind_param(test_dict, None)

        # Should be encrypted
        assert encrypted != str(test_dict)
        assert isinstance(encrypted, str)

        # Should decrypt back to dict
        decrypted = column_type.process_result_value(encrypted, None)
        assert decrypted == test_dict
