"""
Тесты для LLM сервиса.

Тестируем интеграцию с Groq API и генерацию ответов.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from src.domain.entities import Article, LegalAnswer, Message
from src.application.services.llm_service import LLMService


@pytest.fixture
def sample_articles():
    """Примеры статей для тестирования."""
    return [
        Article(
            id=uuid4(),
            number="80",
            title="Расторжение трудового договора по инициативе работника",
            content="Работник имеет право расторгнуть трудовой договор, предупредив об этом работодателя в письменной форме не позднее чем за две недели.",
            chapter="Глава 13. Прекращение трудового договора",
        ),
        Article(
            id=uuid4(),
            number="77",
            title="Отпуск без сохранения заработной платы",
            content="Работнику по семейным обстоятельствам и другим уважительным причинам может быть предоставлен отпуск без сохранения заработной платы.",
            chapter="Глава 19. Отпуска",
        ),
    ]


@pytest.fixture
def llm_service():
    """Фикстура LLM сервиса с тестовым API ключом."""
    with patch("groq.AsyncGroq"):
        return LLMService(api_key="test_api_key")


class TestLLMService:
    """Тесты для LLM сервиса."""

    @pytest.mark.asyncio
    async def test_generate_answer_with_articles(self, sample_articles):
        """Тест: генерация ответа с найденными статьями."""
        # Arrange
        question = "Как уволиться?"
        articles = [sample_articles[0]]

        # Мокируем API ответ от Groq
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="Согласно статье 80 ТК РФ, работник имеет право расторгнуть трудовой договор, предупредив работодателя в письменной форме не позднее чем за две недели."
                )
            )
        ]

        with patch("src.application.services.llm_service.AsyncGroq") as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_groq.return_value = mock_client

            service = LLMService(api_key="test_key")

            # Act
            answer = await service.generate_answer(question, articles)

            # Assert
            assert isinstance(answer, LegalAnswer)
            assert answer.answer
            assert "статье 80" in answer.answer
            assert answer.sources == [80]
            assert answer.confidence > 0.5
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_answer_without_articles(self):
        """Тест: генерация ответа без найденных статей."""
        # Arrange
        question = "Какая погода завтра?"
        articles = []

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="Извините, я не нашёл релевантных статей ТК РФ по вашему вопросу."
                )
            )
        ]

        with patch("src.application.services.llm_service.AsyncGroq") as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_groq.return_value = mock_client

            service = LLMService(api_key="test_key")

            # Act
            answer = await service.generate_answer(question, articles)

            # Assert
            assert answer.confidence < 0.5
            assert not answer.sources

    @pytest.mark.asyncio
    async def test_generate_answer_with_conversation_history(self, sample_articles):
        """Тест: генерация ответа с учётом истории диалога."""
        # Arrange
        question = "А если я не отработаю?"
        articles = [sample_articles[0]]
        history = [
            Message(
                id=uuid4(),
                conversation_id=uuid4(),
                role="user",
                content="Как уволиться?",
            ),
            Message(
                id=uuid4(),
                conversation_id=uuid4(),
                role="assistant",
                content="Согласно статье 80 ТК РФ...",
                sources=[80],
            ),
        ]

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="В случае неотработки двухнедельного срока, увольнение возможно только по соглашению сторон."
                )
            )
        ]

        with patch("src.application.services.llm_service.AsyncGroq") as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_groq.return_value = mock_client

            service = LLMService(api_key="test_key")

            # Act
            await service.generate_answer(question, articles, history)

            # Assert
            # Проверяем, что история была включена в промпт
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            # Должны быть: система + история + текущий вопрос
            assert len(messages) > 2
            # Проверяем, что история передана
            user_messages = [m for m in messages if m["role"] == "user"]
            assert len(user_messages) >= 2

    @pytest.mark.asyncio
    async def test_format_articles_context(self, llm_service, sample_articles):
        """Тест: форматирование промпта с статьями."""
        # Act
        context = llm_service._format_articles_context(sample_articles)

        # Assert
        assert "Статья 80" in context
        assert "Статья 77" in context
        assert "Расторжение трудового договора" in context
        assert "Отпуск без сохранения" in context
        assert "=====" in context  # Разделители

    @pytest.mark.asyncio
    async def test_format_articles_context_empty(self, llm_service):
        """Тест: форматирование с пустым списком статей."""
        # Act
        context = llm_service._format_articles_context([])

        # Assert
        assert "не найдены" in context

    @pytest.mark.asyncio
    async def test_format_history(self, llm_service):
        """Тест: форматирование истории диалога."""
        # Arrange
        history = [
            Message(
                id=uuid4(),
                conversation_id=uuid4(),
                role="user",
                content="Вопрос 1",
            ),
            Message(
                id=uuid4(),
                conversation_id=uuid4(),
                role="assistant",
                content="Ответ 1",
            ),
        ]

        # Act
        formatted = llm_service._format_history(history)

        # Assert
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Вопрос 1"
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["content"] == "Ответ 1"

    @pytest.mark.asyncio
    async def test_extract_article_numbers(self):
        """Тест: извлечение номеров статей из ответа."""
        # Arrange
        from src.application.services.llm_service import extract_article_numbers

        answer_text = "Согласно статьям 80 и 77 ТК РФ, а также статье 81..."

        # Act
        numbers = extract_article_numbers(answer_text)

        # Assert
        assert 80 in numbers
        assert 77 in numbers
        assert 81 in numbers
        assert len(numbers) == 3

    @pytest.mark.asyncio
    async def test_extract_article_numbers_none(self):
        """Тест: извлечение номеров когда их нет."""
        # Arrange
        from src.application.services.llm_service import extract_article_numbers

        answer_text = "Извините, я не нашёл релевантных статей."

        # Act
        numbers = extract_article_numbers(answer_text)

        # Assert
        assert numbers == []

    @pytest.mark.asyncio
    async def test_extract_article_numbers_with_st_abbreviation(self):
        """Тест: извлечение номеров статей с сокращением 'ст.'."""
        # Arrange
        from src.application.services.llm_service import extract_article_numbers

        answer_text = "При увольнении работник имеет ряд прав, закреплённых в Трудовом кодексе РФ. К ним относятся: 1. Получение справки о зарплате и трудовом стаже (ст. 84.1 ТК РФ)"

        # Act
        numbers = extract_article_numbers(answer_text)

        # Assert
        assert 84 in numbers  # ст. 84.1 -> 84

    @pytest.mark.asyncio
    async def test_calculate_confidence_high(self, sample_articles):
        """Тест: высокая уверенность при наличии статей."""
        # Arrange
        question = "Как уволиться?"
        articles = sample_articles

        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Согласно статье 80 и 77 ТК РФ..."))
        ]

        with patch("src.application.services.llm_service.AsyncGroq") as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_groq.return_value = mock_client

            service = LLMService(api_key="test_key")

            # Act
            answer = await service.generate_answer(question, articles)

            # Assert
            # С двумя статьями и упоминанием обеих - высокая уверенность
            assert answer.confidence > 0.8

    @pytest.mark.asyncio
    async def test_calculate_confidence_low(self):
        """Тест: низкая уверенность без статей."""
        # Arrange
        question = "Тест"
        articles = []

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Не могу ответить."))]

        with patch("src.application.services.llm_service.AsyncGroq") as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_groq.return_value = mock_client

            service = LLMService(api_key="test_key")

            # Act
            answer = await service.generate_answer(question, articles)

            # Assert
            # Без статей - низкая уверенность
            assert answer.confidence < 0.5

    @pytest.mark.asyncio
    async def test_handle_api_error(self):
        """Тест: обработка ошибки API."""
        # Arrange
        question = "Тест"
        articles = []

        with patch("src.application.services.llm_service.AsyncGroq") as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            mock_groq.return_value = mock_client

            service = LLMService(api_key="test_key")

            # Act
            answer = await service.generate_answer(question, articles)

            # Assert
            # Сервис должен вернуть fallback ответ вместо исключения
            assert "ошибка" in answer.answer.lower()
            assert answer.confidence == 0.0

    @pytest.mark.asyncio
    async def test_custom_model(self, sample_articles):
        """Тест: использование кастомной модели."""
        # Arrange
        custom_model = "mixtral-8x7b-32768"
        question = "Тест"

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Ответ"))]

        with patch("src.application.services.llm_service.AsyncGroq") as mock_groq:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_groq.return_value = mock_client

            service = LLMService(api_key="test_key", model=custom_model)

            # Act
            await service.generate_answer(question, [sample_articles[0]])

            # Assert
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == custom_model
