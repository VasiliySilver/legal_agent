"""
Middleware для Telegram бота.
Промежуточные обработчики для логирования, rate limiting и инъекции зависимостей.
"""

from src.bot.middlewares.api_client import ApiClientMiddleware
from src.bot.middlewares.logging import LoggingMiddleware
from src.bot.middlewares.throttling import ThrottlingMiddleware

__all__ = [
    "LoggingMiddleware",
    "ThrottlingMiddleware",
    "ApiClientMiddleware",
]