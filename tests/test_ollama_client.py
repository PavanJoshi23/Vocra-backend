import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.ai.ollama_client import (
    generate,
    OllamaUnavailableError,
    OllamaTimeoutError,
)


@pytest.mark.asyncio
async def test_generate_returns_string_on_success():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "Here is your answer."}

    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await generate("qwen2.5:7b", "Tell me about Python.")

    assert result == "Here is your answer."


@pytest.mark.asyncio
async def test_generate_raises_unavailable_on_connect_error():
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client_cls.return_value = mock_client

        with pytest.raises(OllamaUnavailableError):
            await generate("qwen2.5:7b", "test")


@pytest.mark.asyncio
async def test_generate_raises_timeout_on_read_timeout():
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timed out")
        )
        mock_client_cls.return_value = mock_client

        with pytest.raises(OllamaTimeoutError):
            await generate("qwen2.5:7b", "test")


def test_ai_cache_model_importable():
    from app.models.ai_cache import AiCache  # noqa: F401
    assert AiCache.__tablename__ == "ai_cache"


def test_ai_cache_table_created_by_init_db(engine):
    from sqlalchemy import inspect
    inspector = inspect(engine)
    assert "ai_cache" in inspector.get_table_names()
