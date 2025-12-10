"""
Middleware для инъекции API клиента в handlers.
Обеспечивает доступ к REST API во всех обработчиках.
"""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update

from src.bot.api_client import LegalAgentAPIClient

logger = logging.getLogger(__name__)


class ApiClientMiddleware(BaseMiddleware):
    """
    Добавляет API клиент в data для всех handlers.
    Клиент переиспользуется между запросами (singleton pattern).
    """

    def __init__(self, api_client: LegalAgentAPIClient):
        """
        Инициализация middleware.

        Args:
            api_client: Экземпляр API клиента
        """
        super().__init__()
        self.api_client = api_client

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        """
        Инъекция API клиента в data.
        """
        # Добавляем api_client в data
        data["api_client"] = self.api_client
        
        # Вызываем следующий handler
        return await handler(event, data)