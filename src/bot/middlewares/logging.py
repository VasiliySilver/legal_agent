"""
Middleware для логирования всех событий бота.
"""

import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Логирует все входящие обновления и время их обработки.
    """

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        """
        Обработка события с логированием.
        """
        # event это сам Update
        update = event
        
        # Извлекаем информацию о пользователе
        user = None
        if update.message:
            user = update.message.from_user
        elif update.callback_query:
            user = update.callback_query.from_user
        
        user_info = f"User {user.id}" if user else "Unknown user"
        
        # Логируем начало обработки
        start_time = time.time()
        logger.info(f"[{user_info}] Processing update {update.update_id}")
        
        try:
            # Вызываем следующий handler
            result = await handler(event, data)
            
            # Логируем успешное завершение
            elapsed = time.time() - start_time
            logger.info(
                f"[{user_info}] Update {update.update_id} processed in {elapsed:.3f}s"
            )
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            elapsed = time.time() - start_time
            logger.error(
                f"[{user_info}] Update {update.update_id} failed after {elapsed:.3f}s: {e}",
                exc_info=True,
            )
            raise