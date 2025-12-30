import os
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2
from httpx_oauth.oauth2 import BaseOAuth2


# Note: Apple requires a custom client_secret generation (JWT signed with .p8 key)
# which is not standard OAuth2. This is a placeholder for the endpoint.
class AppleOAuth2(BaseOAuth2):
    def __init__(self, client_id, client_secret):
        super().__init__(
            client_id,
            client_secret,
            "https://appleid.apple.com/auth/authorize",
            "https://appleid.apple.com/auth/token",
            name="apple",
        )


google_oauth_client = GoogleOAuth2(
    os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
    os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
)

github_oauth_client = GitHubOAuth2(
    os.getenv("GITHUB_OAUTH_CLIENT_ID", ""),
    os.getenv("GITHUB_OAUTH_CLIENT_SECRET", ""),
)

microsoft_oauth_client = MicrosoftGraphOAuth2(
    os.getenv("MICROSOFT_OAUTH_CLIENT_ID", ""),
    os.getenv("MICROSOFT_OAUTH_CLIENT_SECRET", ""),
)

apple_oauth_client = AppleOAuth2(
    os.getenv("APPLE_OAUTH_CLIENT_ID", ""),
    os.getenv("APPLE_OAUTH_CLIENT_SECRET", ""),
)
