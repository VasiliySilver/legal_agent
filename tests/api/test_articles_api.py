"""Тесты для API endpoints статей."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestArticlesAPI:
    """Тесты для /api/v1/articles endpoints."""
    
    async def test_search_articles_semantic(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест семантического поиска статей."""
        response = await async_client.get(
            "/api/v1/articles",
            params={
                "query": "увольнение по собственному желанию",
                "strategy": "semantic",
                "limit": 5,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "articles" in data
        assert "total" in data
        assert "strategy" in data
        assert data["strategy"] == "semantic"
    
    async def test_search_articles_by_number(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест поиска статьи по номеру."""
        response = await async_client.get(
            "/api/v1/articles",
            params={
                "query": "80",
                "strategy": "by_number",
                "limit": 1,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 0
        assert data["strategy"] == "by_number"
    
    async def test_get_article_by_number(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест получения статьи по номеру через GET."""
        response = await async_client.get("/api/v1/articles/80")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["number"] == "80"
        assert "title" in data
        assert "content" in data
    
    async def test_get_article_not_found(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест получения несуществующей статьи."""
        response = await async_client.get("/api/v1/articles/999")
        
        assert response.status_code == 404
    
    async def test_search_articles_post(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест поиска статей через POST."""
        response = await async_client.post(
            "/api/v1/articles/search",
            json={
                "query": "расторжение договора",
                "strategy": "fulltext",
                "limit": 10,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "articles" in data
        assert data["strategy"] == "fulltext"
    
    async def test_search_articles_invalid_limit(
        self,
        async_client: AsyncClient,
        sample_articles,
    ):
        """Тест валидации лимита результатов."""
        response = await async_client.get(
            "/api/v1/articles",
            params={
                "query": "test",
                "limit": 100,  # Превышает максимум (50)
            },
        )
        
        # Должна быть ошибка валидации
        assert response.status_code == 422
