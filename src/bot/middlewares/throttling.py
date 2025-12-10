"""
Middleware для rate limiting (ограничение частоты запросов).
Защищает от спама и перегрузки.
"""

import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Ограничивает количество запросов от одного пользователя.
    Использует sliding window для подсчёта запросов.
    """

    def __init__(self, rate_limit: int = 10, window: int = 60):
        """
        Инициализация middleware.

        Args:
            rate_limit: Максимум запросов на пользователя
            window: Временное окно в секундах
        """
        super().__init__()
        self.rate_limit = rate_limit
        self.window = window
        # Словарь: user_id -> список timestamp'ов запросов
        self.user_requests: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        """
        Проверка rate limit перед обработкой события.
        """
        # event это сам Update
        update = event
        
        # Извлекаем информацию о пользователе
        user = None
        if update.message:
            user = update.message.from_user
        elif update.callback_query:
            user = update.callback_query.from_user
        
        if not user:
            return await handler(event, data)
        
        user_id = user.id
        current_time = time.time()
        
        # Получаем список запросов пользователя
        user_requests = self.user_requests[user_id]
        
        # Удаляем старые запросы (за пределами окна)
        user_requests[:] = [
            req_time for req_time in user_requests
            if current_time - req_time < self.window
        ]
        
        # Проверяем лимит
        if len(user_requests) >= self.rate_limit:
            logger.warning(
                f"User {user_id} exceeded rate limit "
                f"({len(user_requests)}/{self.rate_limit} in {self.window}s)"
            )
            
            # Отправляем предупреждение пользователю
            if update.message:
                await update.message.answer(
                    "⚠️ Слишком много запросов\\. Пожалуйста, подожди немного\\.",
                    parse_mode="MarkdownV2",
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "⚠️ Слишком много запросов. Подожди немного.",
                    show_alert=True,
                )
            
            # Не вызываем handler
            return None
        
        # Добавляем текущий запрос
        user_requests.append(current_time)
        
        # Вызываем следующий handler
        return await handler(event, data)
    
    def reset_user(self, user_id: int) -> None:
        """
        Сброс счётчика для конкретного пользователя.
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.user_requests:
            del self.user_requests[user_id]
            logger.info(f"Rate limit reset for user {user_id}")