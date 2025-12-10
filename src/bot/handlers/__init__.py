"""
Обработчики команд и сообщений Telegram бота.
"""

from src.bot.handlers.articles import router as articles_router
from src.bot.handlers.conversations import router as conversations_router
from src.bot.handlers.errors import router as errors_router
from src.bot.handlers.questions import router as questions_router
from src.bot.handlers.start import router as start_router

__all__ = [
    "start_router",
    "questions_router",
    "articles_router",
    "conversations_router",
    "errors_router",
]