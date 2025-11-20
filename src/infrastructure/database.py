"""
Инфраструктура: Асинхронное подключение к базе данных PostgreSQL
Использует SQLAlchemy 2.0+ с async/await и asyncpg
Лучшие практики для современных Python веб-приложений
"""

import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy import text
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Базовый класс для всех моделей SQLAlchemy
Base = declarative_base()


# ============================================================================
# КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ
# ============================================================================

def get_database_url() -> str:
    """
    Получить URL подключения к базе данных из переменных окружения
    
    Формат для PostgreSQL (async):
    postgresql+asyncpg://user:password@host:port/database
    
    Формат для SQLite (async):
    sqlite+aiosqlite:///./legal_agent.db
    
    Returns:
        str: URL подключения к БД
    """
    # Пробуем получить из переменных окружения
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        # Heroku использует postgres://, конвертируем в async версию
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return db_url
    
    # Если нет DATABASE_URL, собираем из отдельных переменных
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "legal_agent")
    
    # Для тестов используем SQLite в памяти
    if os.getenv("TESTING") == "true":
        return "sqlite+aiosqlite:///:memory:"
    
    # Для разработки можно использовать SQLite файл
    if os.getenv("USE_SQLITE") == "true":
        return f"sqlite+aiosqlite:///./{db_name}.db"
    
    # PostgreSQL с asyncpg (рекомендуется для production)
    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# ============================================================================
# СОЗДАНИЕ ASYNC ENGINE
# ============================================================================

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
    
    if _async_engine is None:
        database_url = get_database_url()
        
        logger.info(f"Создание асинхронного подключения к БД: {database_url.split('@')[-1] if '@' in database_url else database_url}")
        
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


# ============================================================================
# СОЗДАНИЕ ASYNC СЕССИИ
# ============================================================================

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


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================================================

async def init_database():
    """
    Инициализация базы данных: создание всех таблиц (async)
    
    Использовать при первом запуске приложения
    """
    engine = get_async_engine()
    
    logger.info("Создание таблиц в БД (async)...")
    
    # Импортируем все модели, чтобы они зарегистрировались в Base
    from src.infrastructure.models import (
        ArticleModel,
        ConversationModel,
        MessageModel,
    )
    
    # Создаём таблицы асинхронно
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Таблицы успешно созданы")


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


# ============================================================================
# ПРОВЕРКА ПОДКЛЮЧЕНИЯ
# ============================================================================

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


# ============================================================================
# ЗАКРЫТИЕ СОЕДИНЕНИЙ
# ============================================================================

async def close_database():
    """
    Закрыть все подключения к БД
    
    Использовать при shutdown приложения
    """
    global _async_engine
    
    if _async_engine is not None:
        logger.info("Закрытие подключений к БД...")
        await _async_engine.dispose()
        _async_engine = None
        logger.info("✅ Подключения закрыты")


# ============================================================================
# LIFESPAN ДЛЯ FASTAPI
# ============================================================================

@asynccontextmanager
async def lifespan_manager():
    """
    Lifespan context manager для FastAPI
    
    Использование в FastAPI:
    ```python
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        await init_database()
        yield
        # Shutdown
        await close_database()
    
    app = FastAPI(lifespan=lifespan)
    ```
    """
    # Startup
    logger.info("🚀 Запуск приложения...")
    await init_database()
    await check_connection()
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка приложения...")
    await close_database()


# ============================================================================
# CLI ДЛЯ УПРАВЛЕНИЯ БД
# ============================================================================

if __name__ == "__main__":
    import sys
    import asyncio
    
    async def main():
        if len(sys.argv) < 2:
            print("Использование:")
            print("  python -m src.infrastructure.database init    # Создать таблицы")
            print("  python -m src.infrastructure.database drop    # Удалить таблицы")
            print("  python -m src.infrastructure.database reset   # Пересоздать таблицы")
            print("  python -m src.infrastructure.database check   # Проверить подключение")
            sys.exit(1)
        
        command = sys.argv[1]
        
        if command == "init":
            await init_database()
        elif command == "drop":
            confirm = input("⚠️  Удалить ВСЕ данные? (yes/no): ")
            if confirm.lower() == "yes":
                await drop_database()
            else:
                print("Отменено")
        elif command == "reset":
            confirm = input("⚠️  Пересоздать БД и удалить ВСЕ данные? (yes/no): ")
            if confirm.lower() == "yes":
                await reset_database()
            else:
                print("Отменено")
        elif command == "check":
            if await check_connection():
                print("✅ Подключение к БД работает")
            else:
                print("❌ Ошибка подключения к БД")
                sys.exit(1)
        else:
            print(f"❌ Неизвестная команда: {command}")
            sys.exit(1)
        
        await close_database()
    
    # Запускаем async функцию
    asyncio.run(main())
