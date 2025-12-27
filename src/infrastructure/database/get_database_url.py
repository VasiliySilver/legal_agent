# ============================================================================
# КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ
# ============================================================================


import os


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
