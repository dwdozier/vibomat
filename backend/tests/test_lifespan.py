from unittest.mock import AsyncMock, patch
from backend.app.main import lifespan
from fastapi import FastAPI


async def test_lifespan():
    """Test the application lifespan events."""
    app = FastAPI()
    with patch("backend.app.main.broker") as mock_broker:
        mock_broker.is_worker_process = False
        mock_broker.startup = AsyncMock()
        mock_broker.shutdown = AsyncMock()

        async with lifespan(app):
            # Startup should be called
            mock_broker.startup.assert_awaited_once()

        # Shutdown should be called after exit
        mock_broker.shutdown.assert_awaited_once()


async def test_lifespan_worker_process():
    """Test lifespan when in a worker process."""
    app = FastAPI()
    with patch("backend.app.main.broker") as mock_broker:
        mock_broker.is_worker_process = True
        mock_broker.startup = AsyncMock()
        mock_broker.shutdown = AsyncMock()

        async with lifespan(app):
            mock_broker.startup.assert_not_called()

        mock_broker.shutdown.assert_not_called()
