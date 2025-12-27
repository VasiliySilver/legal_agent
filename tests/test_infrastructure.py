"""
Асинхронные тесты для инфраструктурного слоя (БД, репозитории)
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text


# ============================================================================
# ФИКСТУРЫ ДЛЯ ТЕСТОВ
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Создать async тестовую БД в памяти (SQLite)"""
    from src.infrastructure.database.base import Base
    # Импортируем модели, чтобы они зарегистрировались в Base.metadata

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine):
    """Создать async сессию для тестов"""
    async_session_factory = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def article_repository(test_db_session):
    """Создать репозиторий для статей"""
    from src.infrastructure.repositories import ArticleRepository

    return ArticleRepository(test_db_session)


@pytest_asyncio.fixture(scope="function")
async def conversation_repository(test_db_session):
    """Создать репозиторий для диалогов"""
    from src.infrastructure.repositories import ConversationRepository

    return ConversationRepository(test_db_session)


# ============================================================================
# ТЕСТЫ ДЛЯ DATABASE CONNECTION
# ============================================================================


@pytest.mark.asyncio
async def test_database_connection():
    """Тест подключения к БД"""
    from src.infrastructure.database.engine import get_async_engine

    engine = get_async_engine()
    assert engine is not None

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row[0] == 1


@pytest.mark.asyncio
async def test_create_tables(test_db_engine):
    """Тест создания таблиц в БД"""
    from sqlalchemy import inspect

    def get_table_names(conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async with test_db_engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)

    assert "articles" in tables
    assert "conversations" in tables
    assert "messages" in tables


# ============================================================================
# ТЕСТЫ ДЛЯ ARTICLE MODEL
# ============================================================================


@pytest.mark.asyncio
async def test_article_model_creation(test_db_session):
    """Тест создания модели статьи в БД"""
    from src.infrastructure.models import ArticleModel

    article = ArticleModel(
        number="80",
        title="Расторжение трудового договора",
        content="Работник имеет право расторгнуть трудовой договор...",
        chapter="Глава 13",
    )

    test_db_session.add(article)
    await test_db_session.commit()
    await test_db_session.refresh(article)

    assert article.id is not None
    assert article.created_at is not None


@pytest.mark.asyncio
async def test_article_model_query(test_db_session):
    """Тест запроса статьи из БД"""
    from src.infrastructure.models import ArticleModel

    article = ArticleModel(
        number="115",
        title="Продолжительность отпуска",
        content="28 календарных дней",
        chapter="Глава 19",
    )
    test_db_session.add(article)
    await test_db_session.commit()

    stmt = select(ArticleModel).where(ArticleModel.number == "115")
    result = await test_db_session.execute(stmt)
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.number == "115"


@pytest.mark.asyncio
async def test_article_model_to_entity(test_db_session):
    """Тест преобразования модели БД в доменную сущность"""
    from src.infrastructure.models import ArticleModel

    article_model = ArticleModel(
        number="80", title="Увольнение", content="Контент", chapter="Глава 13"
    )

    article_entity = article_model.to_entity()

    assert article_entity.number == "80"
    assert article_entity.title == "Увольнение"


# ============================================================================
# ТЕСТЫ ДЛЯ CONVERSATION MODEL
# ============================================================================


@pytest.mark.asyncio
async def test_conversation_model_creation(test_db_session):
    """Тест создания модели диалога в БД"""
    from src.infrastructure.models import ConversationModel

    conversation = ConversationModel(user_id="user123")

    test_db_session.add(conversation)
    await test_db_session.commit()
    await test_db_session.refresh(conversation)

    assert conversation.id is not None
    assert conversation.user_id == "user123"


@pytest.mark.asyncio
async def test_message_model_creation(test_db_session):
    """Тест создания модели сообщения в БД"""
    from src.infrastructure.models import ConversationModel, MessageModel

    conversation = ConversationModel(user_id="user123")
    test_db_session.add(conversation)
    await test_db_session.commit()
    await test_db_session.refresh(conversation)

    message = MessageModel(
        conversation_id=conversation.id,
        role="user",
        content="Сколько дней отпуска?",
        metadata_json={},
    )

    test_db_session.add(message)
    await test_db_session.commit()
    await test_db_session.refresh(message)

    assert message.id is not None
    assert message.conversation_id == conversation.id


# ============================================================================
# ТЕСТЫ ДЛЯ ARTICLE REPOSITORY
# ============================================================================


@pytest.mark.asyncio
async def test_article_repository_create(article_repository):
    """Тест создания статьи через репозиторий"""
    from src.domain.entities import Article

    article = Article(
        number="80", title="Увольнение", content="Текст статьи", chapter="Глава 13"
    )

    created = await article_repository.create(article)

    assert created.number == "80"
    assert created.title == "Увольнение"


@pytest.mark.asyncio
async def test_article_repository_get_by_number(article_repository):
    """Тест получения статьи по номеру"""
    from src.domain.entities import Article

    article = Article(
        number="115", title="Отпуск", content="28 дней", chapter="Глава 19"
    )
    await article_repository.create(article)

    found = await article_repository.get_by_number("115")

    assert found is not None
    assert found.number == "115"


@pytest.mark.asyncio
async def test_article_repository_search(article_repository):
    """Тест поиска статей по тексту"""
    from src.domain.entities import Article

    article1 = Article(
        number="80",
        title="Увольнение",
        content="увольнение работника",
        chapter="Глава 13",
    )
    article2 = Article(
        number="115", title="Отпуск", content="отпуск 28 дней", chapter="Глава 19"
    )

    await article_repository.create(article1)
    await article_repository.create(article2)

    results = await article_repository.search("отпуск")

    assert len(results) >= 1
    assert any(a.number == "115" for a in results)


# ============================================================================
# ТЕСТЫ ДЛЯ CONVERSATION REPOSITORY
# ============================================================================


@pytest.mark.asyncio
async def test_conversation_repository_create(conversation_repository):
    """Тест создания диалога через репозиторий"""
    from src.domain.entities import LegalConversation

    conversation = LegalConversation(user_id="user123")
    created = await conversation_repository.create(conversation)

    assert created.user_id == "user123"


@pytest.mark.asyncio
async def test_conversation_repository_get_by_user(conversation_repository):
    """Тест получения диалогов пользователя"""
    from src.domain.entities import LegalConversation

    conv1 = LegalConversation(user_id="user123")
    conv2 = LegalConversation(user_id="user123")
    conv3 = LegalConversation(user_id="user456")

    await conversation_repository.create(conv1)
    await conversation_repository.create(conv2)
    await conversation_repository.create(conv3)

    user_conversations = await conversation_repository.get_by_user_id("user123")

    assert len(user_conversations) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
