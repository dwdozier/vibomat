"""
Distributed lock manager using Redis.

This module provides a Redis-based distributed locking mechanism to prevent race
conditions in concurrent operations across multiple application instances.

Usage:
    from backend.app.core.distributed_lock import DistributedLock

    async with DistributedLock(redis_client, "my_operation", timeout=30):
        # Critical section - only one process can execute at a time
        await perform_operation()
"""

import asyncio
import logging
from typing import Optional

from redis.asyncio import Redis

from backend.app.exceptions import LockAcquisitionError

logger = logging.getLogger(__name__)


class DistributedLock:
    """
    Redis-based distributed lock using SET NX EX for atomic operations.

    This lock ensures that only one process can hold a lock at a time across multiple
    application instances. It uses Redis's SET command with NX (not exists) and EX
    (expiry) options for atomic lock acquisition with automatic expiration.

    Attributes:
        redis: Redis client instance
        lock_name: Name of the lock (used to generate key)
        timeout: Lock expiration time in seconds
        key_prefix: Prefix for Redis key (default: "lock:")
        blocking: Whether to wait for lock availability
        max_wait: Maximum time to wait for lock in seconds (blocking mode only)
        retry_interval: Time between retry attempts in seconds (blocking mode only)
    """

    def __init__(
        self,
        redis: Redis,
        lock_name: str,
        timeout: int,
        key_prefix: str = "lock:",
        blocking: bool = False,
        max_wait: Optional[float] = None,
        retry_interval: float = 0.1,
    ):
        """
        Initialize a distributed lock.

        Args:
            redis: Redis client instance
            lock_name: Name of the lock
            timeout: Lock expiration time in seconds (must be positive)
            key_prefix: Prefix for Redis key
            blocking: If True, wait for lock; if False, fail immediately
            max_wait: Maximum time to wait for lock (blocking mode only)
            retry_interval: Time between retry attempts (blocking mode only)

        Raises:
            ValueError: If timeout is not positive
        """
        if timeout <= 0:
            raise ValueError("Lock timeout must be positive")

        self.redis = redis
        self.lock_name = lock_name
        self.timeout = timeout
        self.key = f"{key_prefix}{lock_name}"
        self.blocking = blocking
        self.max_wait = max_wait
        self.retry_interval = retry_interval
        self._acquired = False

    async def acquire(self) -> bool:
        """
        Attempt to acquire the lock.

        In non-blocking mode, returns immediately if lock cannot be acquired.
        In blocking mode, retries until lock is acquired or max_wait expires.

        Returns:
            True if lock was acquired, False otherwise

        Raises:
            LockAcquisitionError: If lock cannot be acquired or Redis error occurs
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                # Use SET NX EX for atomic lock acquisition with expiration
                acquired = await self.redis.set(self.key, "1", nx=True, ex=self.timeout)

                if acquired:
                    self._acquired = True
                    logger.debug(f"Acquired lock: {self.lock_name}")
                    return True

                # If non-blocking, fail immediately
                if not self.blocking:
                    raise LockAcquisitionError(
                        f"Failed to acquire lock: {self.lock_name} (already held)",
                        details={"lock_name": self.lock_name, "blocking": False},
                    )

                # Check if we've exceeded max wait time
                if self.max_wait is not None:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= self.max_wait:
                        raise LockAcquisitionError(
                            f"Lock acquisition timed out: {self.lock_name} (waited {elapsed:.2f}s)",
                            details={"lock_name": self.lock_name, "max_wait": self.max_wait, "elapsed": elapsed},
                        )

                # Wait before retrying
                await asyncio.sleep(self.retry_interval)

            except (ConnectionError, OSError) as e:
                # Redis connection error
                raise LockAcquisitionError(
                    f"Redis connection error while acquiring lock: {self.lock_name}",
                    details={"lock_name": self.lock_name, "error": str(e)},
                ) from e

    async def release(self) -> None:
        """
        Release the lock by deleting the key from Redis.

        This method is idempotent and won't raise an error if the key doesn't exist
        (e.g., if it already expired or was manually deleted).
        """
        if not self._acquired:
            return

        try:
            deleted = await self.redis.delete(self.key)
            if deleted:
                logger.debug(f"Released lock: {self.lock_name}")
            else:
                logger.warning(f"Lock key already deleted: {self.lock_name}")
            self._acquired = False
        except Exception as e:
            logger.error(f"Error releasing lock {self.lock_name}: {e}", exc_info=True)
            # Don't raise - we want to ensure cleanup continues

    async def __aenter__(self) -> "DistributedLock":
        """
        Enter the async context manager and acquire the lock.

        Returns:
            The DistributedLock instance

        Raises:
            LockAcquisitionError: If lock cannot be acquired
        """
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the async context manager and release the lock.

        The lock is released regardless of whether an exception occurred.
        """
        await self.release()
