from contextlib import asynccontextmanager
from typing import AsyncGenerator
from src.infrastructure.logger import logger


from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.database.engine import get_async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Получить фабрику для создания асинхронных сессий

    Returns:
        async_sessionmaker: Фабрика async сессий
    """
    engine = get_async_engine()
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,  # Явное управление транзакциями
        autoflush=False,  # Явное управление flush
        expire_on_commit=False,  # Не обновлять объекты после commit
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Получить async сессию БД (для dependency injection в FastAPI)

    Использование в FastAPI:
    ```python
    @app.get("/articles")
    async def get_articles(db: AsyncSession = Depends(get_async_session)):
        result = await db.execute(select(Article))
        return result.scalars().all()
    ```

    Yields:
        AsyncSession: SQLAlchemy async сессия
    """
    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager для работы с сессией БД

    Использование:
    ```python
    async with get_db_session() as session:
        result = await session.execute(select(Article))
        articles = result.scalars().all()
    ```

    Yields:
        AsyncSession: SQLAlchemy async сессия
    """
    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка в async сессии БД: {e}")
            raise
        finally:
            await session.close()
