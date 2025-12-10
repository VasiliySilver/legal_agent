"""Тесты для API endpoints диалогов."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestConversationsAPI:
    """Тесты для /api/v1/conversations endpoints."""
    
    async def test_create_conversation(
        self,
        async_client: AsyncClient,
    ):
        """Тест создания нового диалога."""
        response = await async_client.post(
            "/api/v1/conversations",
            json={
                "user_id": "test-user",
                "title": "Вопросы по увольнению",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["user_id"] == "test-user"
        assert data["title"] == "Вопросы по увольнению"
        assert data["message_count"] == 0
    
    async def test_create_conversation_without_title(
        self,
        async_client: AsyncClient,
    ):
        """Тест создания диалога без названия."""
        response = await async_client.post(
            "/api/v1/conversations",
            json={
                "user_id": "test-user",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["user_id"] == "test-user"
        assert data["title"] is None
    
    async def test_get_conversations_list(
        self,
        async_client: AsyncClient,
    ):
        """Тест получения списка диалогов пользователя."""
        # Создаём несколько диалогов
        for i in range(3):
            await async_client.post(
                "/api/v1/conversations",
                json={
                    "user_id": "test-user",
                    "title": f"Диалог {i+1}",
                },
            )
        
        # Получаем список
        response = await async_client.get(
            "/api/v1/conversations",
            params={"user_id": "test-user"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "conversations" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["conversations"]) == 3
    
    async def test_get_conversation_by_id(
        self,
        async_client: AsyncClient,
    ):
        """Тест получения диалога по ID."""
        # Создаём диалог
        create_response = await async_client.post(
            "/api/v1/conversations",
            json={
                "user_id": "test-user",
                "title": "Тестовый диалог",
            },
        )
        conversation_id = create_response.json()["id"]
        
        # Получаем диалог
        response = await async_client.get(f"/api/v1/conversations/{conversation_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == conversation_id
        assert "messages" in data
        assert isinstance(data["messages"], list)
    
    async def test_get_conversation_not_found(
        self,
        async_client: AsyncClient,
    ):
        """Тест получения несуществующего диалога."""
        response = await async_client.get("/api/v1/conversations/non-existent-id")
        
        assert response.status_code == 404
    
    async def test_delete_conversation(
        self,
        async_client: AsyncClient,
    ):
        """Тест удаления диалога."""
        # Создаём диалог
        create_response = await async_client.post(
            "/api/v1/conversations",
            json={
                "user_id": "test-user",
                "title": "Диалог для удаления",
            },
        )
        conversation_id = create_response.json()["id"]
        
        # Удаляем диалог
        response = await async_client.delete(f"/api/v1/conversations/{conversation_id}")
        
        assert response.status_code == 204
        
        # Проверяем, что диалог удалён
        get_response = await async_client.get(f"/api/v1/conversations/{conversation_id}")
        assert get_response.status_code == 404
    
    async def test_update_conversation_title(
        self,
        async_client: AsyncClient,
    ):
        """Тест обновления названия диалога."""
        # Создаём диалог
        create_response = await async_client.post(
            "/api/v1/conversations",
            json={
                "user_id": "test-user",
                "title": "Старое название",
            },
        )
        conversation_id = create_response.json()["id"]
        
        # Обновляем название
        response = await async_client.patch(
            f"/api/v1/conversations/{conversation_id}",
            json={
                "title": "Новое название",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Новое название"
    
    async def test_validation_empty_user_id(
        self,
        async_client: AsyncClient,
    ):
        """Тест валидации пустого user_id."""
        response = await async_client.post(
            "/api/v1/conversations",
            json={
                "user_id": "",
            },
        )
        
        assert response.status_code == 422
