from typing import Optional, Union
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from backend.app.models.user import User, OAuthAccount
from backend.app.core.auth.backend import auth_backend, get_jwt_strategy
from backend.app.core.auth.manager import UserManager
from backend.app.db.session import async_session_maker
from fastapi_users.db import SQLAlchemyUserDatabase


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        # Check if the user is already authenticated via our main cookie
        user = await self._get_current_user(request)
        return user is not None and user.is_superuser

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Union[Response, bool]:
        user = await self._get_current_user(request)
        if user and user.is_superuser:
            # Set a session variable to satisfy any internal checks or state
            # 'token' is the default key used by sqladmin
            request.session.update({"token": "valid_superuser"})
            return True

        return RedirectResponse("/login")

    async def _get_current_user(self, request: Request) -> Optional[User]:
        token = request.cookies.get("fastapiusersauth")
        if not token:
            return None

        async with async_session_maker() as session:
            user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
            user_manager = UserManager(user_db)
            try:
                strategy = get_jwt_strategy()
                user = await strategy.read_token(token, user_manager)
                return user
            except Exception:
                return None


admin_auth = AdminAuth(secret_key=auth_backend.get_strategy().secret)  # type: ignore
