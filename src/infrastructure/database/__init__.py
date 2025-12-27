"""
Инфраструктура: Асинхронное подключение к базе данных PostgreSQL
Использует SQLAlchemy 2.0+ с async/await и asyncpg
Лучшие практики для современных Python веб-приложений
"""

from src.infrastructure.database.check_connection import check_connection
from src.infrastructure.database.close_database import close_database
from src.infrastructure.database.drop_database import drop_database
from src.infrastructure.database.init_database import init_database
from src.infrastructure.load_articles_from_json import load_articles_from_json
from src.infrastructure.database.reset_database import reset_database

# Export submodules for convenience (allow `from src.infrastructure.database import engine`)
from . import engine  # noqa: F401
from . import session  # noqa: F401

# Re-export commonly used symbols from submodules to preserve previous
# package-level API (some modules expect `src.infrastructure.database._async_engine` etc.)
_async_engine = engine._async_engine
get_async_engine = engine.get_async_engine
get_async_session = session.get_async_session
get_async_session_factory = session.get_async_session_factory

__all__ = [
    "check_connection",
    "close_database",
    "drop_database",
    "init_database",
    "load_articles_from_json",
    "reset_database",
    "engine",
    "session",
    "_async_engine",
    "get_async_engine",
    "get_async_session",
    "get_async_session_factory",
]
