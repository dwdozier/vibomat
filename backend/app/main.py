from fastapi import FastAPI, Request, Response
from backend.app.api.v1.api import api_router
from backend.app.core.config import settings
from backend.app.core.tasks import broker
from backend.app.exceptions import ViboMatException
from backend.app.middleware.exception_handler import (
    vibomat_exception_handler,
    generic_exception_handler,
)
from contextlib import asynccontextmanager
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not broker.is_worker_process:
        await broker.startup()
    yield
    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(
    title="Vib-O-Mat API Series 2000",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure rate limiter with Redis storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.REDIS_URL),
    strategy="moving-window",  # Use moving window for more accurate rate limiting
    headers_enabled=True,  # Include rate limit headers in responses
)
app.state.limiter = limiter

# Register exception handlers
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_exception_handler(ViboMatException, vibomat_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]

# Trust proxy headers only from configured trusted IPs (not wildcard)
# This prevents header spoofing attacks from untrusted sources
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.TRUSTED_PROXY_IPS)  # type: ignore

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)  # type: ignore[arg-type]


app.include_router(api_router, prefix="/api/v1")


@app.get("/", name="root")
def root():
    """Root redirect or info."""
    return {"message": "Vib-O-Mat API Series 2000"}


@app.get("/health")
@limiter.limit("100/minute")
def health_check(request: Request, response: Response):
    """Health check endpoint with rate limiting (100 requests/minute)."""
    return {"status": "ok"}
