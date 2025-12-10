"""
Тесты для use case: Поиск статей ТК РФ.

Тестируем различные стратегии поиска статей.
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities import Article
from src.application.use_cases.search_articles import (
    SearchArticlesUseCase,
    ArticleExplorerUseCase,
    SearchStrategy,
)


@pytest.fixture
def mock_article_repository():
    """Мок репозитория статей."""
    repo = AsyncMock()
    repo.get_by_number = AsyncMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    repo.count = AsyncMock()
    return repo


@pytest.fixture
def mock_vector_service():
    """Мок векторного поиска."""
    service = AsyncMock()
    service.find_similar = AsyncMock()
    return service


@pytest.fixture
def sample_articles():
    """Примеры статей для тестирования."""
    return [
        Article(
            id=uuid4(),
            number="80",
            title="Расторжение трудового договора по инициативе работника",
            content="Работник имеет право расторгнуть трудовой договор...",
            chapter="Глава 13. Прекращение трудового договора",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Article(
            id=uuid4(),
            number="77",
            title="Отпуск без сохранения заработной платы",
            content="Работнику по семейным обстоятельствам...",
            chapter="Глава 19. Отпуска",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Article(
            id=uuid4(),
            number="81",
            title="Расторжение трудового договора по инициативе работодателя",
            content="Трудовой договор может быть расторгнут работодателем...",
            chapter="Глава 13. Прекращение трудового договора",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


class TestSearchArticlesUseCase:
    """Тесты для use case поиска статей."""

    @pytest.mark.asyncio
    async def test_search_by_article_number(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: поиск статьи по номеру."""
        # Arrange
        article_number = "80"
        mock_article_repository.get_by_number.return_value = sample_articles[0]

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        article = await use_case.search_by_number(article_number)

        # Assert
        mock_article_repository.get_by_number.assert_called_once_with("80")
        assert article.number == "80"
        assert "инициативе работника" in article.title

    @pytest.mark.asyncio
    async def test_search_by_number_not_found(self, mock_article_repository):
        """Тест: поиск несуществующей статьи."""
        # Arrange
        mock_article_repository.get_by_number.return_value = None

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        article = await use_case.search_by_number("999")

        # Assert
        assert article is None

    @pytest.mark.asyncio
    async def test_search_by_number_empty(self, mock_article_repository):
        """Тест: поиск с пустым номером."""
        # Arrange
        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="Номер статьи не может быть пустым"):
            await use_case.search_by_number("")

    @pytest.mark.asyncio
    async def test_search_by_text(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: полнотекстовый поиск статей."""
        # Arrange
        search_query = "увольнение"
        mock_article_repository.search.return_value = [
            sample_articles[0],
            sample_articles[2],
        ]

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        articles = await use_case.search_by_text(search_query)

        # Assert
        mock_article_repository.search.assert_called_once_with(
            query="увольнение",
            limit=10,
        )
        assert len(articles) == 2
        assert all("Расторжение" in a.title for a in articles)

    @pytest.mark.asyncio
    async def test_search_by_text_with_limit(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: текстовый поиск с лимитом."""
        # Arrange
        mock_article_repository.search.return_value = [sample_articles[0]]

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        await use_case.search_by_text("тест", limit=5)

        # Assert
        call_args = mock_article_repository.search.call_args
        assert call_args.kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_by_text_empty_query(self, mock_article_repository):
        """Тест: текстовый поиск с пустым запросом."""
        # Arrange
        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="Поисковый запрос не может быть пустым"):
            await use_case.search_by_text("")

    @pytest.mark.asyncio
    async def test_semantic_search(
        self,
        mock_article_repository,
        mock_vector_service,
        sample_articles,
    ):
        """Тест: семантический поиск похожих статей."""
        # Arrange
        query = "как прекратить трудовые отношения"
        mock_vector_service.find_similar.return_value = [
            sample_articles[0],
            sample_articles[2],
        ]

        use_case = SearchArticlesUseCase(
            mock_article_repository, vector_service=mock_vector_service
        )

        # Act
        articles = await use_case.semantic_search(query)

        # Assert
        mock_vector_service.find_similar.assert_called_once_with(
            query=query,
            top_k=10,
            threshold=None,
        )
        assert len(articles) == 2

    @pytest.mark.asyncio
    async def test_semantic_search_with_threshold(
        self,
        mock_article_repository,
        mock_vector_service,
        sample_articles,
    ):
        """Тест: семантический поиск с порогом."""
        # Arrange
        mock_vector_service.find_similar.return_value = [sample_articles[0]]

        use_case = SearchArticlesUseCase(
            mock_article_repository, vector_service=mock_vector_service
        )

        # Act
        await use_case.semantic_search("отпуск", top_k=5, threshold=0.7)

        # Assert
        call_args = mock_vector_service.find_similar.call_args
        assert call_args.kwargs["top_k"] == 5
        assert call_args.kwargs["threshold"] == 0.7

    @pytest.mark.asyncio
    async def test_semantic_search_without_vector_service(
        self, mock_article_repository
    ):
        """Тест: семантический поиск без векторного сервиса."""
        # Arrange
        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="Векторный сервис не настроен"):
            await use_case.semantic_search("тест")

    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_article_repository):
        """Тест: поиск без результатов."""
        # Arrange
        search_query = "несуществующая тема"
        mock_article_repository.search.return_value = []

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        articles = await use_case.search_by_text(search_query)

        # Assert
        assert articles == []

    @pytest.mark.asyncio
    async def test_universal_search_by_number(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: универсальный поиск по номеру."""
        # Arrange
        mock_article_repository.get_by_number.return_value = sample_articles[0]

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        articles = await use_case.search("80", strategy=SearchStrategy.BY_NUMBER)

        # Assert
        assert len(articles) == 1
        assert articles[0].number == "80"

    @pytest.mark.asyncio
    async def test_universal_search_fulltext(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: универсальный поиск с текстовой стратегией."""
        # Arrange
        mock_article_repository.search.return_value = [sample_articles[1]]

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        articles = await use_case.search("отпуск", strategy=SearchStrategy.FULLTEXT)

        # Assert
        mock_article_repository.search.assert_called_once()
        assert len(articles) == 1

    @pytest.mark.asyncio
    async def test_universal_search_semantic(
        self,
        mock_article_repository,
        mock_vector_service,
        sample_articles,
    ):
        """Тест: универсальный поиск с семантической стратегией."""
        # Arrange
        mock_vector_service.find_similar.return_value = [sample_articles[0]]

        use_case = SearchArticlesUseCase(
            mock_article_repository, vector_service=mock_vector_service
        )

        # Act
        articles = await use_case.search("уволиться", strategy=SearchStrategy.SEMANTIC)

        # Assert
        mock_vector_service.find_similar.assert_called_once()
        assert len(articles) == 1

    @pytest.mark.asyncio
    async def test_universal_search_semantic_fallback(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: откат на текстовый поиск при отсутствии векторного."""
        # Arrange
        mock_article_repository.search.return_value = [sample_articles[1]]

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act (семантический поиск недоступен, должен быть откат)
        articles = await use_case.search("отпуск", strategy=SearchStrategy.SEMANTIC)

        # Assert
        mock_article_repository.search.assert_called_once()
        assert len(articles) == 1

    @pytest.mark.asyncio
    async def test_get_all_articles(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: получение всех статей."""
        # Arrange
        mock_article_repository.get_all.return_value = sample_articles

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        articles = await use_case.get_all_articles()

        # Assert
        mock_article_repository.get_all.assert_called_once_with(limit=100, offset=0)
        assert len(articles) == 3

    @pytest.mark.asyncio
    async def test_get_all_articles_with_pagination(self, mock_article_repository):
        """Тест: получение статей с пагинацией."""
        # Arrange
        mock_article_repository.get_all.return_value = []

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        await use_case.get_all_articles(limit=50, offset=100)

        # Assert
        call_args = mock_article_repository.get_all.call_args
        assert call_args.kwargs["limit"] == 50
        assert call_args.kwargs["offset"] == 100

    @pytest.mark.asyncio
    async def test_get_articles_by_chapter(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: получение статей по главе."""
        # Arrange
        chapter = "Глава 13"
        mock_article_repository.search.return_value = [
            sample_articles[0],
            sample_articles[2],
        ]

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        articles = await use_case.get_articles_by_chapter(chapter)

        # Assert
        mock_article_repository.search.assert_called_once_with(query=chapter, limit=50)
        assert len(articles) == 2

    @pytest.mark.asyncio
    async def test_count_articles(self, mock_article_repository):
        """Тест: подсчёт статей."""
        # Arrange
        mock_article_repository.count.return_value = 424

        use_case = SearchArticlesUseCase(mock_article_repository)

        # Act
        count = await use_case.count_articles()

        # Assert
        mock_article_repository.count.assert_called_once()
        assert count == 424


class TestArticleExplorerUseCase:
    """Тесты для use case исследования структуры ТК РФ."""

    @pytest.mark.asyncio
    async def test_get_chapters_list(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: получение списка глав."""
        # Arrange
        mock_article_repository.get_all.return_value = sample_articles

        use_case = ArticleExplorerUseCase(mock_article_repository)

        # Act
        chapters = await use_case.get_chapters_list()

        # Assert
        assert len(chapters) == 2
        assert "Глава 13. Прекращение трудового договора" in chapters
        assert "Глава 19. Отпуска" in chapters
        # Проверяем сортировку
        assert chapters == sorted(chapters)

    @pytest.mark.asyncio
    async def test_get_articles_range(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: получение диапазона статей."""
        # Arrange
        mock_article_repository.get_all.return_value = sample_articles

        use_case = ArticleExplorerUseCase(mock_article_repository)

        # Act
        articles = await use_case.get_articles_range("77", "81")

        # Assert
        assert len(articles) == 3
        numbers = [int(a.number) for a in articles]
        assert all(77 <= n <= 81 for n in numbers)

    @pytest.mark.asyncio
    async def test_get_articles_range_reversed(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: диапазон с перевёрнутыми границами."""
        # Arrange
        mock_article_repository.get_all.return_value = sample_articles

        use_case = ArticleExplorerUseCase(mock_article_repository)

        # Act (81 > 77, но должно работать)
        articles = await use_case.get_articles_range("81", "77")

        # Assert
        assert len(articles) == 3

    @pytest.mark.asyncio
    async def test_get_articles_range_invalid(self, mock_article_repository):
        """Тест: некорректный диапазон."""
        # Arrange
        use_case = ArticleExplorerUseCase(mock_article_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="Номера статей должны быть числами"):
            await use_case.get_articles_range("abc", "def")

    @pytest.mark.asyncio
    async def test_get_related_articles(
        self,
        mock_article_repository,
        sample_articles,
    ):
        """Тест: получение близких статей."""
        # Arrange
        mock_article_repository.get_all.return_value = sample_articles

        use_case = ArticleExplorerUseCase(mock_article_repository)

        # Act
        articles = await use_case.get_related_articles("80", context_size=3)

        # Assert
        # Должны быть статьи 77-83 (80 ± 3)
        numbers = [int(a.number) for a in articles]
        assert all(77 <= n <= 83 for n in numbers)

    @pytest.mark.asyncio
    async def test_get_related_articles_invalid_number(self, mock_article_repository):
        """Тест: получение близких статей с некорректным номером."""
        # Arrange
        use_case = ArticleExplorerUseCase(mock_article_repository)

        # Act & Assert
        with pytest.raises(ValueError, match="Номер статьи должен быть числом"):
            await use_case.get_related_articles("abc")
