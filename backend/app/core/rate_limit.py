"""
Rate limiting configuration and utilities.

This module provides the rate limiter instance and decorators for applying
rate limits to endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.app.core.config import settings


# Create limiter instance with Redis storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.REDIS_URL),
    strategy="moving-window",  # Use moving window for more accurate rate limiting
    headers_enabled=True,  # Include rate limit headers in responses
)
