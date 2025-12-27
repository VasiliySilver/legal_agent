# ============================================================================
# ПРОВЕРКА ПОДКЛЮЧЕНИЯ
# ============================================================================
from src.infrastructure.logger import logger


from sqlalchemy import text

from src.infrastructure.database.engine import get_async_engine


async def check_connection() -> bool:
    """
    Проверить подключение к базе данных (async)

    Returns:
        bool: True, если подключение успешно
    """
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Асинхронное подключение к БД успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False
