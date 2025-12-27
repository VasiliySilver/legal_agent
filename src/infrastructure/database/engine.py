from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from src.infrastructure.database.get_database_url import get_database_url
from src.infrastructure.logger import logger


# Глобальный async engine (создаётся один раз)
_async_engine: AsyncEngine | None = None


def get_async_engine() -> AsyncEngine:
    """
    Получить или создать async engine для работы с БД

    Использует async connection pooling для эффективной работы

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    global _async_engine

    # Backwards-compatibility: if package-level `src.infrastructure.database` provided
    # a pre-set `_async_engine` (tests monkeypatch it), use that engine instance.
    try:
        import importlib

        pkg = importlib.import_module("src.infrastructure.database")
        pkg_engine = getattr(pkg, "_async_engine", None)
        if pkg_engine is not None:
            return pkg_engine
    except Exception:
        # ignore import errors / attribute errors
        pass

    if _async_engine is None:
        database_url = get_database_url()

        logger.info(
            f"Создание асинхронного подключения к БД: {database_url.split('@')[-1] if '@' in database_url else database_url}"
        )

        # Настройки для PostgreSQL + asyncpg
        if database_url.startswith("postgresql+asyncpg"):
            _async_engine = create_async_engine(
                database_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=5,  # Размер пула соединений
                max_overflow=10,  # Максимальное количество дополнительных соединений
                pool_pre_ping=True,  # Проверка соединения перед использованием
                pool_recycle=3600,  # Переподключение каждый час
                echo=False,  # Логирование SQL запросов (для отладки включи True)
            )
        # Настройки для SQLite + aiosqlite
        elif database_url.startswith("sqlite+aiosqlite"):
            _async_engine = create_async_engine(
                database_url,
                poolclass=NullPool,  # SQLite не нуждается в пулинге
                echo=False,
            )
        else:
            raise ValueError(f"Неподдерживаемый тип БД: {database_url}")

    return _async_engine
