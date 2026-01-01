from fastapi import FastAPI
from backend.app.api.v1.api import api_router
from backend.app.core.tasks import broker
from contextlib import asynccontextmanager
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


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

# Trust the headers from Nginx

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])  # type: ignore


app.include_router(api_router, prefix="/api/v1")


@app.get("/", name="root")
def root():
    """Root redirect or info."""
    return {"message": "Vib-O-Mat API Series 2000"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
