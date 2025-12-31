from fastapi import FastAPI
from backend.app.api.v1.api import api_router
from backend.app.core.tasks import broker
from contextlib import asynccontextmanager
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from backend.app.db.session import engine
from backend.app.admin.views import UserAdmin, PlaylistAdmin, ServiceConnectionAdmin
from backend.app.admin.auth import admin_auth
from backend.app.core.auth.backend import SECRET


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not broker.is_worker_process:
        await broker.startup()
    yield
    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(
    title="Spotify Playlist Builder API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add Session Middleware for Admin interface

app.add_middleware(SessionMiddleware, secret_key=SECRET)  # type: ignore


# Initialize Admin

admin = Admin(app, engine, authentication_backend=admin_auth, base_url="/admin")

admin.add_view(UserAdmin)

admin.add_view(PlaylistAdmin)

admin.add_view(ServiceConnectionAdmin)


# Trust the headers from Nginx

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])  # type: ignore


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
