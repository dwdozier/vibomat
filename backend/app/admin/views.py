from sqladmin import ModelView, BaseView, expose
from starlette.responses import RedirectResponse
from backend.app.models.user import User
from backend.app.models.playlist import Playlist
from backend.app.models.service_connection import ServiceConnection


class BackToAppView(BaseView):
    name = "Return to Vib-O-Mat"
    icon = "fa-solid fa-arrow-left"

    @expose("/", methods=["GET"])
    async def exit_admin(self, request):
        return RedirectResponse(url=request.url_for("root"))


class UserAdmin(ModelView, model=User):
    column_list = ["id", "email", "is_active", "is_superuser", "is_verified", "is_public"]
    column_details_list = [
        "id",
        "email",
        "is_active",
        "is_superuser",
        "is_verified",
        "is_public",
        "favorite_artists",
        "unskippable_albums",
    ]
    form_columns = [
        "email",
        "is_active",
        "is_superuser",
        "is_verified",
        "is_public",
        "favorite_artists",
        "unskippable_albums",
    ]
    column_searchable_list = ["email"]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class PlaylistAdmin(ModelView, model=Playlist):
    column_list = ["id", "name", "user_id", "public"]
    column_searchable_list = ["name"]
    column_details_list = ["id", "name", "description", "public", "user_id", "source_id"]
    form_columns = ["name", "description", "public", "user_id", "source_id", "content_json"]
    name = "Playlist"
    name_plural = "Playlists"
    icon = "fa-solid fa-music"


class ServiceConnectionAdmin(ModelView, model=ServiceConnection):
    column_list = ["id", "provider_name", "user_id"]
    column_details_list = ["id", "provider_name", "provider_user_id", "user_id", "expires_at"]
    name = "Service Connection"
    name_plural = "Service Connections"
    icon = "fa-solid fa-link"
