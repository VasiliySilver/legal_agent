"""Главное FastAPI приложение для Legal Agent."""

from contextlib import asynccontextmanager
from datetime import datetime
import logging
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.database.close_database import close_database

# Загрузка переменных окружения из .env файла
load_dotenv()

from src.infrastructure.database.check_connection import check_connection  # noqa: E402
from src.infrastructure.database.init_database import (  # noqa: E402
    init_database,
)
from src.api.routes import (  # noqa: E402
    questions_router,
    conversations_router,
    articles_router,
)
from src.api.schemas import HealthCheckResponse, ErrorResponse  # noqa: E402

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN EVENT HANDLER
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.

    Startup:
        - Инициализация базы данных
        - Проверка подключения

    Shutdown:
        - Закрытие подключений к БД
    """
    # Startup
    logger.info("🚀 Запуск Legal Agent API...")

    try:
        await init_database()
        logger.info("✅ База данных инициализирована")

        if await check_connection():
            logger.info("✅ Подключение к БД успешно")
        else:
            logger.error("❌ Ошибка подключения к БД")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}", exc_info=True)

    logger.info("✅ Legal Agent API запущен")

    yield

    # Shutdown
    logger.info("🛑 Остановка Legal Agent API...")
    await close_database()
    logger.info("✅ Legal Agent API остановлен")


# ============================================================================
# СОЗДАНИЕ ПРИЛОЖЕНИЯ
# ============================================================================

app = FastAPI(
    title="Legal Agent API",
    description="REST API для юридического агента по Трудовому Кодексу РФ",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production укажи конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех HTTP запросов."""
    logger.info(f"📨 {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        logger.info(f"📤 {request.method} {request.url.path} - {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка обработки запроса: {e}", exc_info=True)
        raise


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Обработка ошибок валидации."""
    logger.warning(f"Ошибка валидации: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="ValidationError",
            message=str(exc),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка всех неперехваченных исключений."""
    logger.error(f"Необработанное исключение: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="Внутренняя ошибка сервера. Пожалуйста, попробуйте позже.",
        ).model_dump(),
    )


# ============================================================================
# РОУТЫ
# ============================================================================

# Подключаем роуты
app.include_router(questions_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(articles_router, prefix="/api/v1")


# Главная страница
@app.get(
    "/",
    tags=["root"],
    summary="Главная страница",
)
async def root():
    """Главная страница API."""
    return {
        "message": "Legal Agent API",
        "version": "1.0.0",
        "description": "REST API для юридического агента по Трудовому Кодексу РФ",
        "docs": "/docs",
        "health": "/health",
    }


# Health check
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="Проверка работоспособности",
)
async def health_check():
    """
    Проверка работоспособности API и подключения к БД.

    Returns:
        HealthCheckResponse: Статус приложения
    """
    db_status = "ok" if await check_connection() else "error"

    return HealthCheckResponse(
        status="ok",
        database=db_status,
        timestamp=datetime.now(),
    )


# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Для локальной разработки
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоперезагрузка при изменении кода
        log_level="info",
    )
