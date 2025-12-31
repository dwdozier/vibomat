import uuid
from fastapi_users import FastAPIUsers
from backend.app.models.user import User
from backend.app.core.auth.manager import get_user_manager
from backend.app.core.auth.backend import auth_backend

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
current_active_superuser = fastapi_users.current_user(active=True, superuser=True)
