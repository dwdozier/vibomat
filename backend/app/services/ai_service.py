from typing import List, Dict, Any, Optional, cast
from backend.core.ai import generate_playlist, verify_ai_tracks
from backend.core.providers.spotify import SpotifyProvider
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.ai_log import AIInteractionEmbedding
from sqlalchemy import select
import httpx


class AIService:
    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        spotify_provider: Optional[SpotifyProvider] = None,
    ):
        self.db = db
        self.http_client = http_client
        self.spotify_provider = spotify_provider

    def generate(self, prompt: str, count: int = 20, artists: Optional[str] = None) -> Dict[str, Any]:
        full_prompt = prompt
        if artists:
            full_prompt += f". Inspired by artists: {artists}"
        return generate_playlist(full_prompt, count)

    async def verify_tracks(self, tracks: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
        if not self.http_client or not self.spotify_provider:
            # Should not happen in FastAPI, but for core use, raise error
            raise ValueError("HTTP client and Spotify provider required for metadata verification.")
        return await verify_ai_tracks(tracks, http_client=self.http_client, spotify_provider=self.spotify_provider)

    async def store_interaction_embedding(
        self, user_id: Any, prompt: str, embedding: List[float]
    ) -> AIInteractionEmbedding:
        """Store a user prompt and its vector embedding."""
        if not self.db:
            raise ValueError("Database session required for this operation")

        interaction = AIInteractionEmbedding(user_id=user_id, prompt=prompt, embedding=embedding)
        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)
        return interaction

    async def get_nearest_interactions(self, embedding: List[float], limit: int = 5) -> List[AIInteractionEmbedding]:
        """Retrieve the nearest neighbor interactions by vector similarity."""
        if not self.db:
            raise ValueError("Database session required for this operation")

        stmt = (
            select(AIInteractionEmbedding)
            .order_by(AIInteractionEmbedding.embedding.l2_distance(embedding))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(cast(Any, result.scalars().all()))
