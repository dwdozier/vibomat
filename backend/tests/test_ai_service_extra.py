import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.services.ai_service import AIService
from backend.app.models.ai_log import AIInteractionEmbedding
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_store_interaction_embedding():
    mock_db = AsyncMock(spec=AsyncSession)
    service = AIService(db=mock_db)

    user_id = "test-user"
    prompt = "Test prompt"
    embedding = [0.1, 0.2, 0.3]

    result = await service.store_interaction_embedding(user_id, prompt, embedding)

    assert isinstance(result, AIInteractionEmbedding)
    assert result.user_id == user_id
    assert result.prompt == prompt
    assert result.embedding == embedding
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_store_interaction_no_db():
    service = AIService(db=None)
    with pytest.raises(ValueError, match="Database session required"):
        await service.store_interaction_embedding("user", "prompt", [])


@pytest.mark.asyncio
async def test_get_nearest_interactions():
    mock_db = AsyncMock(spec=AsyncSession)
    service = AIService(db=mock_db)

    # Mocking the result of the query
    mock_interaction = MagicMock(spec=AIInteractionEmbedding)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_interaction]
    mock_db.execute.return_value = mock_result

    embedding = [0.1, 0.2, 0.3]
    results = await service.get_nearest_interactions(embedding, limit=5)

    assert len(results) == 1
    assert results[0] == mock_interaction
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_nearest_interactions_no_db():
    service = AIService(db=None)
    with pytest.raises(ValueError, match="Database session required"):
        await service.get_nearest_interactions([])
