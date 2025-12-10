"""Экспорт всех API роутов."""

from src.api.routes.questions import router as questions_router
from src.api.routes.conversations import router as conversations_router
from src.api.routes.articles import router as articles_router

__all__ = [
    "questions_router",
    "conversations_router",
    "articles_router",
]
