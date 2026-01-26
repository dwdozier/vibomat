"""
Tests for distributed lock manager.

This module tests the Redis-based distributed locking mechanism used for preventing
race conditions in concurrent operations like token refresh.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.app.core.distributed_lock import DistributedLock, LockAcquisitionError


class TestDistributedLock:
    """Test basic distributed lock functionality."""

    @pytest.mark.asyncio
    async def test_lock_acquisition_success(self):
        """Verify lock can be acquired successfully."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True  # Simulates successful SET NX EX

        lock = DistributedLock(mock_redis, "test_lock", timeout=10)

        async with lock:
            # Inside context, lock should be acquired
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert call_args[0][0] == "lock:test_lock"  # Key
            assert call_args[1]["nx"] is True  # NX flag
            assert call_args[1]["ex"] == 10  # Expiry

    @pytest.mark.asyncio
    async def test_lock_release_on_exit(self):
        """Verify lock is released when exiting context."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1

        lock = DistributedLock(mock_redis, "test_lock", timeout=10)

        async with lock:
            pass  # Do nothing, just test cleanup

        # After exiting context, delete should be called
        mock_redis.delete.assert_called_once_with("lock:test_lock")

    @pytest.mark.asyncio
    async def test_lock_acquisition_failure_raises_error(self):
        """Verify lock acquisition failure raises LockAcquisitionError."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = False  # Lock already held

        lock = DistributedLock(mock_redis, "test_lock", timeout=10, blocking=False)

        with pytest.raises(LockAcquisitionError) as exc_info:
            async with lock:
                pass

        assert "Failed to acquire lock" in str(exc_info.value)
        assert "test_lock" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lock_with_custom_prefix(self):
        """Verify lock uses custom key prefix."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True

        lock = DistributedLock(mock_redis, "mylock", timeout=5, key_prefix="custom:")

        async with lock:
            call_args = mock_redis.set.call_args
            assert call_args[0][0] == "custom:mylock"


class TestDistributedLockBlocking:
    """Test blocking behavior of distributed lock."""

    @pytest.mark.asyncio
    async def test_blocking_lock_retries(self):
        """Verify blocking lock retries until acquired."""
        mock_redis = AsyncMock()
        # First call fails (locked), second call succeeds
        mock_redis.set.side_effect = [False, True]

        lock = DistributedLock(mock_redis, "test_lock", timeout=10, blocking=True, retry_interval=0.01)

        async with lock:
            pass

        # Should have called set twice (first fail, second success)
        assert mock_redis.set.call_count == 2

    @pytest.mark.asyncio
    async def test_blocking_lock_times_out(self):
        """Verify blocking lock times out after max_wait."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = False  # Always locked

        lock = DistributedLock(mock_redis, "test_lock", timeout=10, blocking=True, max_wait=0.1, retry_interval=0.01)

        with pytest.raises(LockAcquisitionError) as exc_info:
            async with lock:
                pass

        assert "timed out" in str(exc_info.value).lower()


class TestDistributedLockConcurrency:
    """Test lock behavior under concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_lock_acquisition(self):
        """Verify only one of multiple concurrent acquisitions succeeds."""
        mock_redis = AsyncMock()

        # Track which coroutine successfully acquired the lock
        acquired_by = []

        async def try_acquire(task_id: int):
            # First task gets the lock, others fail
            if task_id == 0:
                mock_redis.set.return_value = True
                lock = DistributedLock(mock_redis, "shared_lock", timeout=1, blocking=False)
                try:
                    async with lock:
                        acquired_by.append(task_id)
                        await asyncio.sleep(0.01)
                except LockAcquisitionError:
                    pass
            else:
                mock_redis.set.return_value = False  # Others can't get lock
                lock = DistributedLock(mock_redis, "shared_lock", timeout=1, blocking=False)
                try:
                    async with lock:
                        acquired_by.append(task_id)
                except LockAcquisitionError:
                    pass  # Expected for tasks that don't get the lock

        # Run multiple concurrent acquisition attempts
        await asyncio.gather(
            try_acquire(0),
            try_acquire(1),
            try_acquire(2),
        )

        # Only task 0 should have acquired the lock
        assert len(acquired_by) == 1
        assert acquired_by[0] == 0


class TestDistributedLockEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_lock_with_zero_timeout(self):
        """Verify lock with zero timeout raises error."""
        mock_redis = AsyncMock()

        with pytest.raises(ValueError) as exc_info:
            DistributedLock(mock_redis, "test_lock", timeout=0)

        assert "timeout must be positive" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_lock_with_negative_timeout(self):
        """Verify lock with negative timeout raises error."""
        mock_redis = AsyncMock()

        with pytest.raises(ValueError):
            DistributedLock(mock_redis, "test_lock", timeout=-1)

    @pytest.mark.asyncio
    async def test_lock_handles_redis_connection_error(self):
        """Verify lock handles Redis connection errors gracefully."""
        mock_redis = AsyncMock()
        mock_redis.set.side_effect = ConnectionError("Redis connection failed")

        lock = DistributedLock(mock_redis, "test_lock", timeout=10)

        with pytest.raises(LockAcquisitionError) as exc_info:
            async with lock:
                pass

        assert "Redis connection failed" in str(exc_info.value) or "lock" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_lock_release_handles_deletion_failure(self):
        """Verify lock handles deletion failures during release."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 0  # Key didn't exist (already released)

        lock = DistributedLock(mock_redis, "test_lock", timeout=10)

        # Should not raise exception even if delete returns 0
        async with lock:
            pass

        # Verify delete was still called
        mock_redis.delete.assert_called_once()


class TestDistributedLockContext:
    """Test context manager behavior."""

    @pytest.mark.asyncio
    async def test_lock_releases_on_exception(self):
        """Verify lock is released even when exception occurs in context."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1

        lock = DistributedLock(mock_redis, "test_lock", timeout=10)

        with pytest.raises(RuntimeError):
            async with lock:
                raise RuntimeError("Something went wrong")

        # Lock should still be released
        mock_redis.delete.assert_called_once_with("lock:test_lock")

    @pytest.mark.asyncio
    async def test_lock_context_returns_lock_object(self):
        """Verify entering context returns lock object."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True

        lock = DistributedLock(mock_redis, "test_lock", timeout=10)

        async with lock as acquired_lock:
            assert acquired_lock is lock
