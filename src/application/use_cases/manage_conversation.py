"""
Use Case: Управление диалогами с пользователями.

Создание диалогов, добавление сообщений, получение истории.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from src.domain.entities import LegalAnswer, LegalConversation, LegalQuery, Message
from src.infrastructure.repositories import ConversationRepository


class ManageConversationUseCase:
    """
    Use Case для управления диалогами пользователей.
    
    Основные операции:
    - Создание нового диалога
    - Добавление сообщения в диалог
    - Получение истории диалога
    - Получение диалогов пользователя
    """

    def __init__(self, conversation_repository: ConversationRepository):
        """
        Инициализация use case.

        Args:
            conversation_repository: Репозиторий для работы с диалогами
        """
        self.repository = conversation_repository

    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> LegalConversation:
        """
        Создать новый диалог для пользователя.

        Args:
            user_id: ID пользователя
            title: Название диалога (опционально)

        Returns:
            LegalConversation: Созданный диалог

        Raises:
            ValueError: Если user_id пустой
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id не может быть пустым")

        # Создаём новый диалог
        conversation = LegalConversation(
            id=uuid4(),
            user_id=user_id.strip(),
            title=title,
            started_at=datetime.now(),
            messages=[],
        )

        # Сохраняем в БД
        saved_conversation = await self.repository.create(conversation)

        return saved_conversation

    async def add_user_message(
        self,
        conversation_id: int,
        query: LegalQuery,
    ) -> Message:
        """
        Добавить сообщение пользователя в диалог.

        Args:
            conversation_id: ID диалога
            query: Запрос пользователя

        Returns:
            Message: Добавленное сообщение

        Raises:
            ValueError: Если диалог не найден
        """
        # Проверяем существование диалога
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Диалог {conversation_id} не найден")

        # Добавляем сообщение
        updated_conversation = await self.repository.add_message(
            conversation_id, query
        )

        # Возвращаем последнее добавленное сообщение
        return updated_conversation.messages[-1]

    async def add_assistant_message(
        self,
        conversation_id: int,
        answer: LegalAnswer,
    ) -> Message:
        """
        Добавить сообщение ассистента в диалог.

        Args:
            conversation_id: ID диалога
            answer: Ответ ассистента

        Returns:
            Message: Добавленное сообщение

        Raises:
            ValueError: Если диалог не найден
        """
        # Проверяем существование диалога
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Диалог {conversation_id} не найден")

        # Добавляем сообщение
        updated_conversation = await self.repository.add_message(
            conversation_id, answer
        )

        # Возвращаем последнее добавленное сообщение
        return updated_conversation.messages[-1]

    async def get_conversation(self, conversation_id: int) -> LegalConversation:
        """
        Получить диалог по ID.

        Args:
            conversation_id: ID диалога

        Returns:
            LegalConversation: Диалог с историей сообщений

        Raises:
            ValueError: Если диалог не найден
        """
        conversation = await self.repository.get_by_id(conversation_id)

        if not conversation:
            raise ValueError(f"Диалог {conversation_id} не найден")

        return conversation

    async def get_conversation_history(
        self, conversation_id: int
    ) -> list[Message]:
        """
        Получить историю сообщений диалога.

        Args:
            conversation_id: ID диалога

        Returns:
            Список сообщений

        Raises:
            ValueError: Если диалог не найден
        """
        conversation = await self.get_conversation(conversation_id)
        return conversation.messages

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[LegalConversation]:
        """
        Получить все диалоги пользователя.

        Args:
            user_id: ID пользователя
            limit: Максимальное количество диалогов
            offset: Смещение для пагинации

        Returns:
            Список диалогов пользователя
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id не может быть пустым")

        conversations = await self.repository.get_by_user_id(
            user_id=user_id.strip(),
            limit=limit,
            offset=offset,
        )

        return conversations

    async def get_latest_conversation(
        self, user_id: str
    ) -> Optional[LegalConversation]:
        """
        Получить последний диалог пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Последний диалог или None
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id не может быть пустым")

        return await self.repository.get_latest_by_user_id(user_id.strip())

    async def delete_conversation(self, conversation_id: int) -> bool:
        """
        Удалить диалог.

        Args:
            conversation_id: ID диалога

        Returns:
            True, если диалог удалён
        """
        return await self.repository.delete(conversation_id)

    async def update_conversation(self, conversation_id: int, title: Optional[str] = None) -> Optional[LegalConversation]:
        """
        Обновить диалог.

        Args:
            conversation_id: ID диалога
            title: Новое название (опционально)

        Returns:
            LegalConversation: Обновлённый диалог или None, если не найден

        Raises:
            ValueError: Если диалог не найден
        """
        # Получаем существующий диалог
        conversation = await self.repository.get_by_id(conversation_id)
        
        if not conversation:
            raise ValueError(f"Диалог {conversation_id} не найден")
        
        # Обновляем поля
        if title is not None:
            conversation.title = title
        
        conversation.updated_at = datetime.now()
        
        # Сохраняем изменения
        updated_conversation = await self.repository.update(conversation)
        
        return updated_conversation

    async def get_conversation_count(self, user_id: str) -> int:
        """
        Получить количество диалогов пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Количество диалогов
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id не может быть пустым")

        return await self.repository.count_by_user_id(user_id.strip())


