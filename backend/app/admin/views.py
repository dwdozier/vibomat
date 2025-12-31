from sqladmin import ModelView
from backend.app.models.user import User
from backend.app.models.playlist import Playlist
from backend.app.models.service_connection import ServiceConnection


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.is_active, User.is_superuser]
    column_searchable_list = [User.email]
    icon = "fa-solid fa-user"


class PlaylistAdmin(ModelView, model=Playlist):
    column_list = [Playlist.id, Playlist.name, Playlist.user_id]
    column_searchable_list = [Playlist.name]
    icon = "fa-solid fa-music"


class ServiceConnectionAdmin(ModelView, model=ServiceConnection):
    column_list = [ServiceConnection.id, ServiceConnection.provider_name, ServiceConnection.user_id]
    icon = "fa-solid fa-link"
