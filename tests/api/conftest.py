"""Конфигурация тестов для API."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
import os

from src.api.main import app
from src.infrastructure.database import Base, get_async_session
from src.infrastructure.models import ArticleModel
from src.domain.entities import Article


# Переопределяем DATABASE_URL для тестов
os.environ["TESTING"] = "true"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Создать тестовый async engine."""
    import tempfile
    
    # Создаём временный файл для БД
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    # Используем обычный путь, настройки через connect_args
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
        connect_args={
            "check_same_thread": False,
            "timeout": 10,
        },
    )
    
    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Закрываем engine
    await engine.dispose()
    
    # Удаляем временный файл
    try:
        os.unlink(db_path)
        # Удаляем WAL files если они есть
        try:
            os.unlink(f"{db_path}-wal")
            os.unlink(f"{db_path}-shm")
        except:
            pass
    except:
        pass


@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine):
    """Создать фабрику тестовых сессий."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(scope="function")
async def sample_articles(test_session_factory) -> AsyncGenerator[list[Article], None]:
    """Создать тестовые статьи в БД."""
    articles_data = [
        Article(
            number="80",
            title="Расторжение трудового договора по инициативе работника",
            content="Работник имеет право расторгнуть трудовой договор...",
            chapter="Глава 13",
        ),
        Article(
            number="81",
            title="Расторжение трудового договора по инициативе работодателя",
            content="Трудовой договор может быть расторгнут работодателем...",
            chapter="Глава 13",
        ),
        Article(
            number="140",
            title="Сроки расчета при увольнении",
            content="При прекращении трудового договора выплата всех сумм...",
            chapter="Глава 21",
        ),
    ]
    
    # Сохраняем в БД
    async with test_session_factory() as session:
        for article_data in articles_data:
            article_model = ArticleModel.from_entity(article_data)
            session.add(article_model)
        await session.commit()
    
    yield articles_data
    
    # Очищаем БД после теста
    async with test_session_factory() as session:
        await session.execute(ArticleModel.__table__.delete())
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_engine, test_session_factory, sample_articles) -> AsyncGenerator[AsyncClient, None]:
    """
    Создать async HTTP клиент для тестирования API.
    
    Переопределяет dependency для get_async_session и настраивает vector service.
    """
    # Импортируем модуль database чтобы подменить engine
    import src.infrastructure.database as db_module
    from unittest.mock import MagicMock
    
    # Сохраняем оригинальный engine
    original_engine = db_module._async_engine
    
    # Подменяем глобальный engine на тестовый
    db_module._async_engine = test_engine
    
    # Импортируем зависимости и сервисы
    from src.api.dependencies import get_vector_service, get_llm_service
    from src.application.services.vector_service import VectorService, VectorBackend
    from src.application.services.llm_service import LLMService
    
    # Создаём и настраиваем vector service с индексом
    vector_service = VectorService(backend=VectorBackend.FAISS)
    await vector_service.build_index(sample_articles)
    
    # Создаём мок для LLM service
    mock_llm_service = MagicMock(spec=LLMService)
    
    # Переопределяем зависимости
    def override_get_vector_service():
        return vector_service
    
    def override_get_llm_service():
        return mock_llm_service
    
    app.dependency_overrides[get_vector_service] = override_get_vector_service
    app.dependency_overrides[get_llm_service] = override_get_llm_service
    
    # Создаём клиент
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Восстанавливаем оригинальный engine
    db_module._async_engine = original_engine
    
    # Очищаем переопределения
    app.dependency_overrides.clear()

