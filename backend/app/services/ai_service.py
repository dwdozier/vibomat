from typing import List, Dict, Any, Optional
from backend.core.ai import generate_playlist, verify_ai_tracks


class AIService:
    def generate(
        self, prompt: str, count: int = 20, artists: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        full_prompt = prompt
        if artists:
            full_prompt += f". Inspired by artists: {artists}"
        return generate_playlist(full_prompt, count)

    def verify_tracks(self, tracks: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
        return verify_ai_tracks(tracks)
