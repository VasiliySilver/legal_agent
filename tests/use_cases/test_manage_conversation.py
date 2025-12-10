"""
Тесты для use case: Управление диалогами.

Тестируем создание, получение и управление диалогами пользователей.
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities import (
    LegalAnswer,
    LegalConversation,
    LegalQuery,
    Message,
)
from src.application.use_cases.manage_conversation import ManageConversationUseCase


@pytest.fixture
def mock_conversation_repository():
    """Мок репозитория диалогов."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.add_message = AsyncMock()
    repo.get_by_user_id = AsyncMock()
    repo.get_latest_by_user_id = AsyncMock()
    repo.delete = AsyncMock()
    repo.count_by_user_id = AsyncMock()
    return repo


@pytest.fixture
def sample_conversation():
    """Пример диалога."""
    conv_id = uuid4()
    return LegalConversation(
        id=conv_id,
        user_id="user_123",
        started_at=datetime.now(),
        messages=[
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="user",
                content="Как уволиться?",
                timestamp=datetime.now(),
            ),
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="assistant",
                content="Согласно статье 80 ТК РФ...",
                timestamp=datetime.now(),
                sources=[80],
            ),
        ],
    )


class TestManageConversationUseCase:
    """Тесты для use case управления диалогами."""

    @pytest.mark.asyncio
    async def test_create_new_conversation(self, mock_conversation_repository):
        """Тест: создание нового диалога."""
        # Arrange
        user_id = "user_123"
        expected_conv = LegalConversation(
            id=uuid4(),
            user_id=user_id,
            started_at=datetime.now(),
            messages=[],
        )
        mock_conversation_repository.create.return_value = expected_conv

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        conversation = await use_case.create_conversation(user_id)

        # Assert
        mock_conversation_repository.create.assert_called_once()
        assert conversation.user_id == user_id
        assert conversation.messages == []

    @pytest.mark.asyncio
    async def test_create_conversation_empty_user_id(
        self, mock_conversation_repository
    ):
        """Тест: создание диалога с пустым user_id."""
        # Arrange
        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="user_id не может быть пустым"):
            await use_case.create_conversation("")

        with pytest.raises(ValueError, match="user_id не может быть пустым"):
            await use_case.create_conversation("   ")

    @pytest.mark.asyncio
    async def test_add_user_message(
        self,
        mock_conversation_repository,
        sample_conversation,
    ):
        """Тест: добавление сообщения пользователя."""
        # Arrange
        conv_id = 123
        query = LegalQuery(
            question="Ещё вопрос...",
            user_id="user_123",
        )

        # Диалог существует
        mock_conversation_repository.get_by_id.return_value = sample_conversation

        # После добавления
        new_message = Message(
            id=uuid4(),
            conversation_id=sample_conversation.id,
            role="user",
            content=query.question,
            timestamp=datetime.now(),
        )
        updated_conversation = LegalConversation(
            id=sample_conversation.id,
            user_id=sample_conversation.user_id,
            started_at=sample_conversation.started_at,
            messages=sample_conversation.messages + [new_message],
        )
        mock_conversation_repository.add_message.return_value = updated_conversation

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        added_message = await use_case.add_user_message(conv_id, query)

        # Assert
        mock_conversation_repository.get_by_id.assert_called_once_with(conv_id)
        mock_conversation_repository.add_message.assert_called_once_with(conv_id, query)
        assert added_message.role == "user"
        assert added_message.content == query.question

    @pytest.mark.asyncio
    async def test_add_assistant_message(
        self,
        mock_conversation_repository,
        sample_conversation,
    ):
        """Тест: добавление сообщения ассистента."""
        # Arrange
        conv_id = 123
        answer = LegalAnswer(
            answer="Ответ ассистента",
            sources=[80],
            confidence=0.9,
        )

        mock_conversation_repository.get_by_id.return_value = sample_conversation

        new_message = Message(
            id=uuid4(),
            conversation_id=sample_conversation.id,
            role="assistant",
            content=answer.answer,
            timestamp=datetime.now(),
            sources=answer.sources,
        )
        updated_conversation = LegalConversation(
            id=sample_conversation.id,
            user_id=sample_conversation.user_id,
            started_at=sample_conversation.started_at,
            messages=sample_conversation.messages + [new_message],
        )
        mock_conversation_repository.add_message.return_value = updated_conversation

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        added_message = await use_case.add_assistant_message(conv_id, answer)

        # Assert
        mock_conversation_repository.add_message.assert_called_once()
        assert added_message.role == "assistant"
        assert added_message.sources == answer.sources

    @pytest.mark.asyncio
    async def test_add_message_to_nonexistent_conversation(
        self, mock_conversation_repository
    ):
        """Тест: добавление сообщения в несуществующий диалог."""
        # Arrange
        conv_id = 999
        query = LegalQuery(question="Тест", user_id="user_123")

        mock_conversation_repository.get_by_id.return_value = None

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="Диалог .* не найден"):
            await use_case.add_user_message(conv_id, query)

    @pytest.mark.asyncio
    async def test_get_conversation(
        self,
        mock_conversation_repository,
        sample_conversation,
    ):
        """Тест: получение диалога по ID."""
        # Arrange
        conv_id = 123
        mock_conversation_repository.get_by_id.return_value = sample_conversation

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        conversation = await use_case.get_conversation(conv_id)

        # Assert
        mock_conversation_repository.get_by_id.assert_called_once_with(conv_id)
        assert conversation.user_id == sample_conversation.user_id
        assert len(conversation.messages) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, mock_conversation_repository):
        """Тест: запрос несуществующего диалога."""
        # Arrange
        fake_id = 999
        mock_conversation_repository.get_by_id.return_value = None

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="Диалог .* не найден"):
            await use_case.get_conversation(fake_id)

    @pytest.mark.asyncio
    async def test_get_conversation_history(
        self,
        mock_conversation_repository,
        sample_conversation,
    ):
        """Тест: получение истории диалога."""
        # Arrange
        conv_id = 123
        mock_conversation_repository.get_by_id.return_value = sample_conversation

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        history = await use_case.get_conversation_history(conv_id)

        # Assert
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_get_user_conversations(
        self,
        mock_conversation_repository,
        sample_conversation,
    ):
        """Тест: получение всех диалогов пользователя."""
        # Arrange
        user_id = "user_123"
        conversations = [sample_conversation]
        mock_conversation_repository.get_by_user_id.return_value = conversations

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        result = await use_case.get_user_conversations(user_id)

        # Assert
        mock_conversation_repository.get_by_user_id.assert_called_once_with(
            user_id=user_id,
            limit=10,
            offset=0,
        )
        assert len(result) == 1
        assert result[0].user_id == user_id

    @pytest.mark.asyncio
    async def test_get_user_conversations_with_pagination(
        self, mock_conversation_repository
    ):
        """Тест: получение диалогов с пагинацией."""
        # Arrange
        user_id = "user_123"
        mock_conversation_repository.get_by_user_id.return_value = []

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        await use_case.get_user_conversations(user_id, limit=5, offset=10)

        # Assert
        mock_conversation_repository.get_by_user_id.assert_called_once_with(
            user_id=user_id,
            limit=5,
            offset=10,
        )

    @pytest.mark.asyncio
    async def test_get_latest_conversation(
        self,
        mock_conversation_repository,
        sample_conversation,
    ):
        """Тест: получение последнего диалога пользователя."""
        # Arrange
        user_id = "user_123"
        mock_conversation_repository.get_latest_by_user_id.return_value = (
            sample_conversation
        )

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        conversation = await use_case.get_latest_conversation(user_id)

        # Assert
        mock_conversation_repository.get_latest_by_user_id.assert_called_once_with(
            user_id
        )
        assert conversation == sample_conversation

    @pytest.mark.asyncio
    async def test_get_latest_conversation_none(self, mock_conversation_repository):
        """Тест: получение последнего диалога, когда его нет."""
        # Arrange
        user_id = "user_123"
        mock_conversation_repository.get_latest_by_user_id.return_value = None

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        conversation = await use_case.get_latest_conversation(user_id)

        # Assert
        assert conversation is None

    @pytest.mark.asyncio
    async def test_delete_conversation(self, mock_conversation_repository):
        """Тест: удаление диалога."""
        # Arrange
        conv_id = 123
        mock_conversation_repository.delete.return_value = True

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        result = await use_case.delete_conversation(conv_id)

        # Assert
        mock_conversation_repository.delete.assert_called_once_with(conv_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_conversation_count(self, mock_conversation_repository):
        """Тест: подсчёт диалогов пользователя."""
        # Arrange
        user_id = "user_123"
        mock_conversation_repository.count_by_user_id.return_value = 5

        use_case = ManageConversationUseCase(mock_conversation_repository)

        # Act
        count = await use_case.get_conversation_count(user_id)

        # Assert
        mock_conversation_repository.count_by_user_id.assert_called_once_with(user_id)
        assert count == 5
