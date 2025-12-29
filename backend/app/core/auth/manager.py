import uuid
import os
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from backend.app.models.user import User
from backend.app.db.session import get_async_session
from fastapi_users.db import SQLAlchemyUserDatabase

SECRET = os.getenv("FASTAPI_SECRET", "DEVELOPMENT_SECRET_CHANGE_ME")


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")


async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
