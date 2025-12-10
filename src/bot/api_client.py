"""
HTTP клиент для взаимодействия с REST API Legal Agent.
"""

import logging
from typing import Any, Optional

from aiohttp import ClientError, ClientSession, ClientTimeout

from src.bot.config import BotConfig

logger = logging.getLogger(__name__)


class LegalAgentAPIClient:
    """
    Async HTTP клиент для REST API.
    Поддерживает context manager для автоматического управления сессией.
    """

    def __init__(self, config: BotConfig):
        """
        Инициализация клиента.

        Args:
            config: Конфигурация бота с URL API и таймаутами
        """
        self.base_url = config.api_v1_url
        self.timeout = config.api_timeout
        self._session: Optional[ClientSession] = None

    async def __aenter__(self) -> "LegalAgentAPIClient":
        """Вход в async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Выход из async context manager."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Создание HTTP сессии если её нет."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self.timeout)
            self._session = ClientSession(timeout=timeout)

    async def close(self) -> None:
        """Закрытие HTTP сессии."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def ask_question(
        self,
        question: str,
        conversation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Отправка вопроса в API для получения юридического ответа.

        Args:
            question: Вопрос пользователя
            conversation_id: ID диалога для продолжения беседы

        Returns:
            Словарь с ответом, статьями и метаданными

        Raises:
            Exception: При ошибке API или сети
        """
        await self._ensure_session()

        payload = {"question": question}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            async with self._session.post(
                f"{self.base_url}/answer",
                json=payload,
            ) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(
                    f"Получен ответ от API для вопроса: {question[:50]}..."
                )
                return result

        except ClientError as e:
            logger.error(f"Network error при запросе к API: {e}")
            raise Exception(f"Ошибка сети при обращении к API: {e}")

        except Exception as e:
            logger.error(f"API error: {e}")
            raise Exception(f"Ошибка API: {e}")

    async def search_articles(
        self,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Поиск статей ТК РФ по запросу или номеру.

        Args:
            query: Поисковый запрос или номер статьи
            limit: Максимальное количество результатов

        Returns:
            Словарь со списком найденных статей

        Raises:
            Exception: При ошибке API или сети
        """
        await self._ensure_session()

        try:
            async with self._session.get(
                f"{self.base_url}/articles/search",
                params={"query": query, "limit": limit},
            ) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Найдено статей: {len(result.get('articles', []))}")
                return result

        except ClientError as e:
            logger.error(f"Network error при поиске статей: {e}")
            raise Exception(f"Ошибка сети при поиске: {e}")

        except Exception as e:
            logger.error(f"API error при поиске: {e}")
            raise Exception(f"Ошибка поиска: {e}")

    async def get_conversation_history(
        self,
        conversation_id: str,
    ) -> dict[str, Any]:
        """
        Получение истории диалога.

        Args:
            conversation_id: ID диалога

        Returns:
            Словарь с историей сообщений

        Raises:
            Exception: При ошибке API или сети
        """
        await self._ensure_session()

        try:
            async with self._session.get(
                f"{self.base_url}/conversations/{conversation_id}",
            ) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Получена история диалога: {conversation_id}")
                return result

        except ClientError as e:
            logger.error(f"Network error при получении истории: {e}")
            raise Exception(f"Ошибка сети: {e}")

        except Exception as e:
            logger.error(f"API error при получении истории: {e}")
            raise Exception(f"Ошибка получения истории: {e}")

    async def create_conversation(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Создание нового диалога.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Словарь с данными нового диалога

        Raises:
            Exception: При ошибке API или сети
        """
        await self._ensure_session()

        try:
            async with self._session.post(
                f"{self.base_url}/conversations",
                json={"user_id": user_id},
            ) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Создан новый диалог для пользователя: {user_id}")
                return result

        except ClientError as e:
            logger.error(f"Network error при создании диалога: {e}")
            raise Exception(f"Ошибка сети: {e}")

        except Exception as e:
            logger.error(f"API error при создании диалога: {e}")
            raise Exception(f"Ошибка создания диалога: {e}")