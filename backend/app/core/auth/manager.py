import uuid
import re
from typing import Optional, Any, Dict
from fastapi import Depends, Request, Response, HTTPException
from fastapi_users import BaseUserManager, UUIDIDMixin
from backend.app.models.user import User, OAuthAccount
from backend.app.db.session import get_async_session
from fastapi_users.db import SQLAlchemyUserDatabase
from backend.app.core.utils.email import send_email
from backend.app.core.config import settings
from sqlalchemy import select

SECRET = settings.SECRET_KEY


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def validate_handle(self, handle: Optional[str], user: Optional[User] = None):
        if handle is None:
            return

        if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", handle):
            raise HTTPException(
                status_code=400,
                detail=("Handle must be 3-20 characters and only contain letters, " "numbers, underscores, or dashes."),
            )

        # Check uniqueness
        query = select(User).where(User.handle == handle)
        if user:
            query = query.where(User.id != user.id)

        # Cast to SQLAlchemyUserDatabase to access session (Ty check fix)
        # In a real app we might want a cleaner interface, but this works for now.
        if isinstance(self.user_db, SQLAlchemyUserDatabase):
            result = await self.user_db.session.execute(query)
            if result.unique().scalar_one_or_none():
                raise HTTPException(status_code=400, detail="This handle is already taken.")
        else:
            # Fallback or error if using a different DB backend
            pass

    async def on_before_register(self, user_create: Any, request: Optional[Request] = None):
        if hasattr(user_create, "handle"):
            await self.validate_handle(user_create.handle)

    async def on_before_update(self, user: User, update_dict: Dict[str, Any], request: Optional[Request] = None):
        if "handle" in update_dict:
            await self.validate_handle(update_dict["handle"], user)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        await self._promote_if_admin(user)

        welcome_body = (
            f"Greetings, Citizen! You have successfully registered with the "
            f"Vib-O-Mat Series 2000. Your ID is {user.id}."
        )
        welcome_html = """
<div style="font-family: sans-serif; padding: 20px; border: 4px solid #2D3436;
border-radius: 10px; background-color: #FFFDF5;">
    <h1 style="color: #50C8C6;">Vib-O-Mat</h1>
    <p>Greetings, Citizen!</p>
    <p>You have successfully registered with the <strong>Vib-O-Mat Series 2000</strong>.</p>
    <p>Prepare for high-fidelity playlist generation!</p>
    <hr style="border: 1px dashed #2D3436;" />
    <p style="font-size: 0.8em; color: #666;">Vib-O-Mat Corp © 1962</p>
</div>
"""
        await send_email(
            to_email=user.email,
            subject="Welcome to the Vib-O-Mat!",
            body=welcome_body,
            html_body=welcome_html,
        )

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ):
        await self._promote_if_admin(user)

    async def _promote_if_admin(self, user: User):
        if user.email in settings.ADMIN_EMAILS and not user.is_superuser:
            await self.user_db.update(user, {"is_superuser": True, "is_verified": True})


async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
