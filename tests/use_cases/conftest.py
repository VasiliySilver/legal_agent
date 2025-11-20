"""
Общие фикстуры для тестов use cases.

Содержит моки репозиториев, сервисов и примеры данных.
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities import Article, LegalConversation, Message


@pytest.fixture
def sample_articles():
    """Примеры статей ТК РФ для тестирования."""
    return [
        Article(
            id=uuid4(),
            number="77",
            title="Отпуск без сохранения заработной платы",
            content="Работнику по семейным обстоятельствам и другим уважительным причинам может быть предоставлен отпуск без сохранения заработной платы.",
            chapter="Глава 19. Отпуска",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Article(
            id=uuid4(),
            number="80",
            title="Расторжение трудового договора по инициативе работника",
            content="Работник имеет право расторгнуть трудовой договор, предупредив об этом работодателя в письменной форме не позднее чем за две недели.",
            chapter="Глава 13. Прекращение трудового договора",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Article(
            id=uuid4(),
            number="81",
            title="Расторжение трудового договора по инициативе работодателя",
            content="Трудовой договор может быть расторгнут работодателем в случаях...",
            chapter="Глава 13. Прекращение трудового договора",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def sample_conversation():
    """Пример диалога с историей сообщений."""
    conv_id = uuid4()
    return LegalConversation(
        id=conv_id,
        user_id="user_123",
        started_at=datetime.now(),
        messages=[
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="user",
                content="Как уволиться?",
                timestamp=datetime.now(),
            ),
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="assistant",
                content="Согласно статье 80 ТК РФ...",
                timestamp=datetime.now(),
                sources=[80],
            ),
        ],
    )


@pytest.fixture
def mock_article_repository():
    """Мок репозитория статей."""
    repo = AsyncMock()
    repo.search = AsyncMock()
    repo.get_by_number = AsyncMock()
    repo.get_all = AsyncMock()
    repo.count = AsyncMock()
    return repo


@pytest.fixture
def mock_conversation_repository():
    """Мок репозитория диалогов."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.add_message = AsyncMock()
    repo.get_by_user_id = AsyncMock()
    repo.get_latest_by_user_id = AsyncMock()
    repo.delete = AsyncMock()
    repo.count_by_user_id = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    """Мок LLM сервиса."""
    service = AsyncMock()
    service.generate_answer = AsyncMock()
    return service


@pytest.fixture
def mock_vector_service():
    """Мок векторного поиска."""
    service = AsyncMock()
    service.find_similar = AsyncMock()
    service.create_index = AsyncMock()
    service.save_index = AsyncMock()
    service.load_index = AsyncMock()
    return service
