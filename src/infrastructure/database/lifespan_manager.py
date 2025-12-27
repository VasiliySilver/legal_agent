from src.infrastructure.database.check_connection import check_connection
from src.infrastructure.database.close_database import close_database
from src.infrastructure.logger import logger


from contextlib import asynccontextmanager

from src.infrastructure.database.init_database import init_database


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
