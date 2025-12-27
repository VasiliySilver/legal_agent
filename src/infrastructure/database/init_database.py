from src.infrastructure.database.base import Base
from src.infrastructure.logger import logger
from src.infrastructure.database.engine import get_async_engine

# Импортируем модели, чтобы они зарегистрировались в Base.metadata
import src.infrastructure.models  # noqa: F401


async def init_database():
    """
    Инициализация базы данных: создание всех таблиц (async)

    Использовать при первом запуске приложения
    """
    engine = get_async_engine()

    logger.info("Создание таблиц в БД (async)...")

    # Импортируем все модели, чтобы они зарегистрировались в Base

    # Создаём таблицы асинхронно
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ Таблицы успешно созданы")
