"""Тесты для API endpoints вопросов."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from src.domain.entities import LegalAnswer


@pytest.mark.asyncio
class TestQuestionsAPI:
    """Тесты для /api/v1/questions endpoints."""

    async def test_ask_quick_question(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест быстрого ответа на вопрос."""
        # Мокаем LLM сервис для генерации ответа
        from src.api.main import app
        from src.api.dependencies import get_llm_service

        mock_llm = AsyncMock()
        mock_llm.generate_answer.return_value = LegalAnswer(
            answer="Работник имеет право расторгнуть трудовой договор по ст. 80 ТК РФ",
            context=sample_articles[:1],
            sources=[80],
            article_numbers=["80"],
            confidence=0.9,
        )

        # Переопределяем dependency
        app.dependency_overrides[get_llm_service] = lambda: mock_llm

        response = await async_client.post(
            "/api/v1/questions/quick",
            json={
                "question": "Как уволиться по собственному желанию?",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "articles" in data
        assert "metadata" in data
        assert data["metadata"]["confidence"] >= 0.0
        assert len(data["articles"]) > 0

    async def test_ask_question_with_conversation(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест вопроса с сохранением в диалог."""
        # Мокаем LLM сервис для генерации ответа
        from src.api.main import app
        from src.api.dependencies import get_llm_service

        mock_llm = AsyncMock()
        mock_llm.generate_answer.return_value = LegalAnswer(
            answer="Ответ на вопрос о способах увольнения",
            context=sample_articles[:2],
            sources=[80, 81],
            article_numbers=["80", "81"],
            confidence=0.85,
        )

        # Переопределяем dependency
        app.dependency_overrides[get_llm_service] = lambda: mock_llm

        response = await async_client.post(
            "/api/v1/questions",
            json={
                "question": "Какие есть способы увольнения?",
                "user_id": "test-user",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "answer" in data
        assert "conversation_id" in data
        assert data["conversation_id"] is not None
        assert len(data["articles"]) > 0
        assert data["metadata"]["sources_count"] > 0

    async def test_ask_question_validation_error(
        self,
        async_client: AsyncClient,
    ):
        """Тест валидации пустого вопроса."""
        response = await async_client.post(
            "/api/v1/questions/quick",
            json={
                "question": "",  # Пустой вопрос
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_ask_question_too_long(
        self,
        async_client: AsyncClient,
    ):
        """Тест валидации слишком длинного вопроса."""
        long_question = "x" * 1001  # Превышает максимум (1000)

        response = await async_client.post(
            "/api/v1/questions/quick",
            json={
                "question": long_question,
            },
        )

        assert response.status_code == 422
