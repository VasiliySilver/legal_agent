from src.infrastructure.database.base import Base
from src.infrastructure.logger import logger
from src.infrastructure.database.engine import get_async_engine


async def drop_database():
    """
    Удалить все таблицы из БД (async)

    ⚠️ ОСТОРОЖНО: Удаляет ВСЕ данные!
    Использовать только для разработки/тестов
    """
    engine = get_async_engine()

    logger.warning("⚠️  Удаление всех таблиц из БД...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    logger.info("✅ Таблицы успешно удалены")
