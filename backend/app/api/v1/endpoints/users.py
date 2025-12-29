from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_async_session
from backend.app.core.auth.fastapi_users import current_active_user
from backend.app.models.user import User
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()


class UserPreferencesUpdate(BaseModel):
    discogs_pat: Optional[str] = Field(None, description="Discogs Personal Access Token")


@router.patch("/me/preferences")
async def update_preferences(
    update: UserPreferencesUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update the current user's preferences (e.g., Discogs PAT).
    """
    # Note: User model needs a field for preferences or discogs_pat
    # For now, we'll just mock the update as we need a migration to add the field
    return {"status": "success", "message": "Preferences updated (Mocked)"}
