from fastapi import APIRouter
from backend.app.api.v1.endpoints import playlists, integrations, users
from backend.app.core.auth.fastapi_users import fastapi_users
from backend.app.core.auth.backend import auth_backend
from backend.app.schemas.user import UserRead, UserCreate
from backend.app.core.auth.oauth import (
    google_oauth_client,
    github_oauth_client,
    microsoft_oauth_client,
    apple_oauth_client,
)
import os

api_router = APIRouter()

# Auth routes
api_router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
api_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# OAuth Routes
api_router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        os.getenv("FASTAPI_SECRET", "devsecret"),
        associate_by_email=True,
    ),
    prefix="/auth/google",
    tags=["auth"],
)
api_router.include_router(
    fastapi_users.get_oauth_router(
        github_oauth_client,
        auth_backend,
        os.getenv("FASTAPI_SECRET", "devsecret"),
        associate_by_email=True,
    ),
    prefix="/auth/github",
    tags=["auth"],
)
api_router.include_router(
    fastapi_users.get_oauth_router(
        microsoft_oauth_client,
        auth_backend,
        os.getenv("FASTAPI_SECRET", "devsecret"),
        associate_by_email=True,
    ),
    prefix="/auth/microsoft",
    tags=["auth"],
)
api_router.include_router(
    fastapi_users.get_oauth_router(
        apple_oauth_client,
        auth_backend,
        os.getenv("FASTAPI_SECRET", "devsecret"),
        associate_by_email=True,
    ),
    prefix="/auth/apple",
    tags=["auth"],
)

# Application routes
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
