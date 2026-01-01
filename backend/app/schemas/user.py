import uuid
from typing import List, Any, Optional
from pydantic import BaseModel, ConfigDict
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    is_public: bool
    favorite_artists: List[str]
    unskippable_albums: List[Any]


class UserCreate(schemas.BaseUserCreate):
    is_public: bool = True
    favorite_artists: List[str] = []
    unskippable_albums: List[Any] = []


class UserUpdate(schemas.BaseUserUpdate):
    is_public: Optional[bool] = None
    favorite_artists: Optional[List[str]] = None
    unskippable_albums: Optional[List[Any]] = None


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str  # We might want to mask this in a real app
    favorite_artists: List[str]
    unskippable_albums: List[Any]
    is_public: bool

    model_config = ConfigDict(from_attributes=True)
