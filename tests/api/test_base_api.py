"""Тесты для базовых API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBaseAPI:
    """Тесты для базовых endpoints."""
    
    async def test_root_endpoint(self, async_client: AsyncClient):
        """Тест главной страницы API."""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Legal Agent API"
    
    async def test_health_check(self, async_client: AsyncClient):
        """Тест healthcheck endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data
        assert data["status"] == "ok"
    
    async def test_openapi_docs(self, async_client: AsyncClient):
        """Тест доступности OpenAPI документации."""
        response = await async_client.get("/docs")
        
        assert response.status_code == 200
    
    async def test_openapi_schema(self, async_client: AsyncClient):
        """Тест доступности OpenAPI схемы."""
        response = await async_client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "Legal Agent API"
