"""
Тесты для HTTP клиента к REST API.
"""

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientError, ClientResponseError

from src.bot.api_client import LegalAgentAPIClient
from src.bot.config import BotConfig


@pytest.fixture
def bot_config():
    """Фикстура: конфигурация бота."""
    with patch.dict(
        "os.environ",
        {"BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"},
    ):
        return BotConfig()


@pytest.fixture
def api_client(bot_config):
    """Фикстура: API клиент."""
    return LegalAgentAPIClient(bot_config)


@pytest.mark.asyncio
async def test_api_client_initialization(api_client, bot_config):
    """Тест: клиент инициализируется с правильными параметрами."""
    assert api_client.base_url == bot_config.api_v1_url
    assert api_client.timeout == bot_config.api_timeout


@pytest.mark.asyncio
async def test_ask_question_success(api_client):
    """Тест: успешный запрос на ответ по вопросу."""
    mock_response = {
        "answer": "Согласно статье 21 ТК РФ...",
        "articles": [{"number": "21", "title": "Основные права работника"}],
        "confidence": 0.95,
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aenter__.return_value.status = 200

        result = await api_client.ask_question("Какие права у работника?")

        assert result["answer"] == "Согласно статье 21 ТК РФ..."
        assert len(result["articles"]) == 1
        assert result["confidence"] == 0.95


@pytest.mark.asyncio
async def test_ask_question_with_conversation_id(api_client):
    """Тест: запрос с указанием conversation_id."""
    mock_response = {
        "answer": "Продолжаю ответ...",
        "articles": [],
        "confidence": 0.8,
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aenter__.return_value.status = 200

        result = await api_client.ask_question(
            "Расскажи подробнее",
            conversation_id="conv-123",
        )

        # Проверяем, что conversation_id был передан в запросе
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["conversation_id"] == "conv-123"


@pytest.mark.asyncio
async def test_ask_question_api_error(api_client):
    """Тест: обработка ошибки API."""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.status = 500
        mock_post.return_value.__aenter__.return_value.text = AsyncMock(
            return_value="Internal Server Error"
        )

        with pytest.raises(Exception) as exc_info:
            await api_client.ask_question("Тест")

        # Проверяем что ошибка содержит "API error" или "api error"
        error_message = str(exc_info.value).lower()
        assert "api error" in error_message


@pytest.mark.asyncio
async def test_ask_question_network_error(api_client):
    """Тест: обработка сетевой ошибки."""
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.side_effect = ClientError("Network error")

        with pytest.raises(Exception) as exc_info:
            await api_client.ask_question("Тест")

        assert "network" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_articles_by_number(api_client):
    """Тест: поиск статьи по номеру."""
    mock_response = {
        "articles": [
            {
                "number": "21",
                "title": "Основные права работника",
                "content": "Работник имеет право на...",
            }
        ]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aenter__.return_value.status = 200

        result = await api_client.search_articles("21")

        assert len(result["articles"]) == 1
        assert result["articles"][0]["number"] == "21"


@pytest.mark.asyncio
async def test_get_conversation_history(api_client):
    """Тест: получение истории диалога."""
    mock_response = {
        "id": "conv-123",
        "messages": [
            {"role": "user", "content": "Вопрос 1"},
            {"role": "assistant", "content": "Ответ 1"},
        ],
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_get.return_value.__aenter__.return_value.status = 200

        result = await api_client.get_conversation_history("conv-123")

        assert result["id"] == "conv-123"
        assert len(result["messages"]) == 2


@pytest.mark.asyncio
async def test_create_conversation(api_client):
    """Тест: создание нового диалога."""
    mock_response = {
        "id": "conv-new",
        "user_id": "user-123",
        "created_at": "2025-12-10T12:00:00Z",
    }

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_post.return_value.__aenter__.return_value.status = 201

        result = await api_client.create_conversation("user-123")

        assert result["id"] == "conv-new"
        assert result["user_id"] == "user-123"


@pytest.mark.asyncio
async def test_client_context_manager(api_client):
    """Тест: клиент работает как async context manager."""
    async with api_client as client:
        assert client._session is not None

    # После выхода из контекста сессия должна быть закрыта
    assert api_client._session is None or api_client._session.closed