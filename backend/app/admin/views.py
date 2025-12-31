from sqladmin import ModelView
from backend.app.models.user import User
from backend.app.models.playlist import Playlist
from backend.app.models.service_connection import ServiceConnection


class UserAdmin(ModelView, model=User):
    column_list = ["id", "email", "is_active", "is_superuser", "is_verified"]
    column_details_list = ["id", "email", "is_active", "is_superuser", "is_verified"]
    form_columns = ["email", "is_active", "is_superuser", "is_verified"]
    column_searchable_list = ["email"]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class PlaylistAdmin(ModelView, model=Playlist):
    column_list = ["id", "name", "user_id"]
    column_searchable_list = ["name"]
    column_details_list = ["id", "name", "description", "public", "user_id"]
    name = "Playlist"
    name_plural = "Playlists"
    icon = "fa-solid fa-music"


class ServiceConnectionAdmin(ModelView, model=ServiceConnection):
    column_list = ["id", "provider_name", "user_id"]
    column_details_list = ["id", "provider_name", "provider_user_id", "user_id", "expires_at"]
    name = "Service Connection"
    name_plural = "Service Connections"
    icon = "fa-solid fa-link"
