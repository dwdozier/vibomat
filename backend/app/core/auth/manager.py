import uuid
import os
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from backend.app.models.user import User, OAuthAccount
from backend.app.db.session import get_async_session
from fastapi_users.db import SQLAlchemyUserDatabase
from backend.app.core.utils.email import send_email

SECRET = os.getenv("FASTAPI_SECRET", "DEVELOPMENT_SECRET_CHANGE_ME")


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
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


async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
