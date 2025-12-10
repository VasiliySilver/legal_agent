"""
Тесты для use case: Ответ на юридический вопрос.

Тестируем основной use case приложения - генерацию ответов
на вопросы пользователей с использованием статей ТК РФ.
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities import Article, LegalAnswer, LegalQuery, Message
from src.application.use_cases.answer_legal_question import (
    AnswerLegalQuestionUseCase,
)


@pytest.fixture
def mock_article_repository():
    """Мок репозитория статей."""
    repo = AsyncMock()
    repo.search = AsyncMock()
    repo.get_by_number = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.fixture
def mock_conversation_repository():
    """Мок репозитория диалогов."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    """Мок LLM сервиса."""
    service = AsyncMock()
    service.generate_answer = AsyncMock()
    return service


@pytest.fixture
def mock_vector_service():
    """Мок векторного поиска."""
    service = AsyncMock()
    service.find_similar = AsyncMock()
    return service


@pytest.fixture
def sample_articles():
    """Примеры статей ТК РФ."""
    return [
        Article(
            id=uuid4(),
            number="77",
            title="Отпуск без сохранения заработной платы",
            content="Работнику по семейным обстоятельствам и другим уважительным причинам...",
            chapter="Глава 19. Отпуска",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Article(
            id=uuid4(),
            number="80",
            title="Расторжение трудового договора по инициативе работника",
            content="Работник имеет право расторгнуть трудовой договор, предупредив об этом работодателя...",
            chapter="Глава 13. Прекращение трудового договора",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


class TestAnswerLegalQuestionUseCase:
    """Тесты для use case ответа на юридический вопрос."""

    @pytest.mark.asyncio
    async def test_answer_question_with_relevant_articles(
        self,
        mock_article_repository,
        mock_llm_service,
        sample_articles,
    ):
        """Тест: успешный ответ на вопрос с найденными статьями."""
        # Arrange
        query = LegalQuery(
            question="Как взять отпуск без сохранения зарплаты?",
            user_id="user_123",
        )

        mock_article_repository.search.return_value = [sample_articles[0]]
        mock_llm_service.generate_answer.return_value = LegalAnswer(
            answer="Согласно статье 77 ТК РФ, работник может взять отпуск без сохранения зарплаты...",
            sources=[77],
            confidence=0.95,
        )

        use_case = AnswerLegalQuestionUseCase(
            article_repository=mock_article_repository,
            llm_service=mock_llm_service,
        )

        # Act
        answer = await use_case.execute(query)

        # Assert
        mock_article_repository.search.assert_called_once()
        mock_llm_service.generate_answer.assert_called_once()
        assert answer.answer
        assert answer.sources
        assert answer.confidence > 0.8

    @pytest.mark.asyncio
    async def test_answer_question_no_articles_found(
        self,
        mock_article_repository,
        mock_llm_service,
    ):
        """Тест: вопрос без релевантных статей."""
        # Arrange
        query = LegalQuery(
            question="Какая погода завтра?",
            user_id="user_123",
        )

        mock_article_repository.search.return_value = []
        mock_llm_service.generate_answer.return_value = LegalAnswer(
            answer="Извините, я не нашёл релевантных статей ТК РФ по вашему вопросу.",
            sources=[],
            confidence=0.1,
        )

        use_case = AnswerLegalQuestionUseCase(
            article_repository=mock_article_repository,
            llm_service=mock_llm_service,
        )

        # Act
        answer = await use_case.execute(query)

        # Assert
        mock_article_repository.search.assert_called_once()
        assert answer.confidence < 0.5
        assert not answer.sources

    @pytest.mark.asyncio
    async def test_answer_question_with_vector_search(
        self,
        mock_article_repository,
        mock_vector_service,
        mock_llm_service,
        sample_articles,
    ):
        """Тест: использование векторного поиска."""
        # Arrange
        query = LegalQuery(
            question="Хочу уволиться",
            user_id="user_123",
        )

        mock_vector_service.find_similar.return_value = [sample_articles[1]]
        mock_llm_service.generate_answer.return_value = LegalAnswer(
            answer="Согласно статье 80 ТК РФ...",
            sources=[80],
            confidence=0.92,
        )

        use_case = AnswerLegalQuestionUseCase(
            article_repository=mock_article_repository,
            llm_service=mock_llm_service,
            vector_service=mock_vector_service,
        )

        # Act
        answer = await use_case.execute(query)

        # Assert
        mock_vector_service.find_similar.assert_called_once()
        # Текстовый поиск не должен вызываться, если векторный успешен
        mock_article_repository.search.assert_not_called()
        assert answer.sources == [80]

    @pytest.mark.asyncio
    async def test_answer_question_vector_fallback_to_text(
        self,
        mock_article_repository,
        mock_vector_service,
        mock_llm_service,
        sample_articles,
    ):
        """Тест: откат на текстовый поиск при ошибке векторного."""
        # Arrange
        query = LegalQuery(
            question="отпуск",
            user_id="user_123",
        )

        # Векторный поиск падает
        mock_vector_service.find_similar.side_effect = Exception("Vector error")
        mock_article_repository.search.return_value = [sample_articles[0]]
        mock_llm_service.generate_answer.return_value = LegalAnswer(
            answer="Согласно статье 77...",
            sources=[77],
            confidence=0.85,
        )

        use_case = AnswerLegalQuestionUseCase(
            article_repository=mock_article_repository,
            llm_service=mock_llm_service,
            vector_service=mock_vector_service,
        )

        # Act
        answer = await use_case.execute(query)

        # Assert
        mock_vector_service.find_similar.assert_called_once()
        mock_article_repository.search.assert_called_once()
        assert answer.answer
        assert answer.sources

    @pytest.mark.asyncio
    async def test_answer_question_with_conversation_context(
        self,
        mock_article_repository,
        mock_conversation_repository,
        mock_llm_service,
        sample_articles,
    ):
        """Тест: ответ с учётом контекста диалога."""
        # Arrange
        conv_id = 123
        query = LegalQuery(
            question="А если я не отработаю 2 недели?",
            user_id="user_123",
            conversation_id=conv_id,
        )

        # История диалога
        from src.domain.entities import LegalConversation

        conversation = LegalConversation(
            id=uuid4(),
            user_id="user_123",
            started_at=datetime.now(),
            messages=[
                Message(
                    id=uuid4(),
                    conversation_id=uuid4(),
                    role="user",
                    content="Как уволиться?",
                    timestamp=datetime.now(),
                ),
                Message(
                    id=uuid4(),
                    conversation_id=uuid4(),
                    role="assistant",
                    content="Согласно статье 80 ТК РФ...",
                    timestamp=datetime.now(),
                    sources=[80],
                ),
            ],
        )

        mock_conversation_repository.get_by_id.return_value = conversation
        mock_article_repository.search.return_value = [sample_articles[1]]
        mock_llm_service.generate_answer.return_value = LegalAnswer(
            answer="В случае неотработки...",
            sources=[80],
            confidence=0.9,
        )

        use_case = AnswerLegalQuestionUseCase(
            article_repository=mock_article_repository,
            llm_service=mock_llm_service,
            conversation_repository=mock_conversation_repository,
        )

        # Act
        await use_case.execute(query, conversation_id=conv_id)

        # Assert
        mock_conversation_repository.get_by_id.assert_called_once_with(conv_id)
        # Убедимся, что история была передана в LLM
        call_args = mock_llm_service.generate_answer.call_args
        assert call_args.kwargs["history"] is not None
        assert len(call_args.kwargs["history"]) == 2

    @pytest.mark.asyncio
    async def test_answer_empty_question(
        self,
        mock_article_repository,
        mock_llm_service,
    ):
        """Тест: пустой вопрос вызывает ошибку валидации."""
        # Arrange
        from pydantic import ValidationError

        # Act & Assert
        # Pydantic должен отклонить пустой вопрос на уровне валидации
        with pytest.raises(ValidationError):
            LegalQuery(
                question="",
                user_id="user_123",
            )

    @pytest.mark.asyncio
    async def test_answer_question_custom_top_k(
        self,
        mock_article_repository,
        mock_llm_service,
        sample_articles,
    ):
        """Тест: настройка количества результатов поиска."""
        # Arrange
        query = LegalQuery(
            question="Тестовый вопрос",
            user_id="user_123",
        )

        mock_article_repository.search.return_value = sample_articles
        mock_llm_service.generate_answer.return_value = LegalAnswer(
            answer="Ответ",
            sources=[77, 80],
            confidence=0.88,
        )

        use_case = AnswerLegalQuestionUseCase(
            article_repository=mock_article_repository,
            llm_service=mock_llm_service,
        )

        # Act
        await use_case.execute(query, top_k=10)

        # Assert
        # Проверяем, что поиск был вызван с правильным лимитом
        call_args = mock_article_repository.search.call_args
        assert call_args.kwargs["limit"] == 10
