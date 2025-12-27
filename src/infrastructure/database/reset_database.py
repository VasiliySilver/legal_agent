from src.infrastructure.logger import logger
from src.infrastructure.database.drop_database import drop_database
from src.infrastructure.database.init_database import init_database


async def reset_database():
    """
    Пересоздать базу данных (удалить + создать) - async

    ⚠️ ОСТОРОЖНО: Удаляет ВСЕ данные!
    Использовать только для разработки/тестов
    """
    logger.warning("⚠️  Пересоздание базы данных...")
    await drop_database()
    await init_database()
    logger.info("✅ База данных пересоздана")
