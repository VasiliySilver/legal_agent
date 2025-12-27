# ============================================================================
# ЗАКРЫТИЕ СОЕДИНЕНИЙ
# ============================================================================


from src.infrastructure.logger import logger
import src.infrastructure.database.engine as engine_module


async def close_database():
    """
    Закрыть все подключения к БД

    Использовать при shutdown приложения
    """
    async_engine = engine_module.get_async_engine()

    if async_engine is not None:
        logger.info("Закрытие подключений к БД...")
        await async_engine.dispose()
        # Обнуляем синглтон в модуле engine (best-effort)
        try:
            engine_module._async_engine = None
        except Exception:
            logger.debug("Не удалось сбросить _async_engine атрибут в engine_module")
        logger.info("✅ Подключения закрыты")
