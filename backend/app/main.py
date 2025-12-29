from fastapi import FastAPI
from backend.app.api.v1.endpoints import playlists

app = FastAPI(
    title="Spotify Playlist Builder API",
    version="0.1.0",
)

app.include_router(playlists.router, prefix="/api/v1/playlists", tags=["playlists"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
