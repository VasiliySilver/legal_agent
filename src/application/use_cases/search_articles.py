"""
Use Case: Поиск статей ТК РФ.

Различные стратегии поиска: по номеру, полнотекстовый, семантический.
"""

from enum import Enum
from typing import Optional

from src.domain.entities import Article
from src.application.services.vector_service import VectorService
from src.infrastructure.repositories import ArticleRepository


class SearchStrategy(str, Enum):
    """Стратегии поиска статей."""

    BY_NUMBER = "by_number"  # Точный поиск по номеру статьи
    FULLTEXT = "fulltext"  # Полнотекстовый поиск в БД
    SEMANTIC = "semantic"  # Семантический поиск через векторы


class SearchArticlesUseCase:
    """
    Use Case для поиска статей ТК РФ.
    
    Поддерживает разные стратегии поиска:
    - По номеру статьи (точное совпадение)
    - Полнотекстовый поиск (PostgreSQL ILIKE)
    - Семантический поиск (векторные эмбеддинги)
    """

    def __init__(
        self,
        article_repository: ArticleRepository,
        vector_service: Optional[VectorService] = None,
    ):
        """
        Инициализация use case.

        Args:
            article_repository: Репозиторий для работы со статьями
            vector_service: Сервис векторного поиска (опционально)
        """
        self.repository = article_repository
        self.vector_service = vector_service

    async def search_by_number(self, number: str) -> Optional[Article]:
        """
        Поиск статьи по точному номеру.

        Args:
            number: Номер статьи (например, "80", "77")

        Returns:
            Article или None, если не найдена

        Raises:
            ValueError: Если номер пустой
        """
        if not number or not number.strip():
            raise ValueError("Номер статьи не может быть пустым")

        return await self.repository.get_by_number(number.strip())

    async def search_by_text(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Article]:
        """
        Полнотекстовый поиск статей.

        Ищет в заголовках, содержимом и номерах статей.

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            Список найденных статей

        Raises:
            ValueError: Если запрос пустой
        """
        if not query or not query.strip():
            raise ValueError("Поисковый запрос не может быть пустым")

        return await self.repository.search(
            query=query.strip(),
            limit=limit,
        )

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: Optional[float] = None,
    ) -> list[Article]:
        """
        Семантический поиск похожих статей.

        Использует векторные эмбеддинги для поиска статей,
        близких по смыслу к запросу.

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            threshold: Порог схожести (опционально)

        Returns:
            Список похожих статей

        Raises:
            ValueError: Если запрос пустой или векторный сервис недоступен
        """
        if not query or not query.strip():
            raise ValueError("Поисковый запрос не может быть пустым")

        if not self.vector_service:
            raise ValueError(
                "Векторный сервис не настроен. "
                "Используйте search_by_text() для полнотекстового поиска."
            )

        return await self.vector_service.find_similar(
            query=query.strip(),
            top_k=top_k,
            threshold=threshold,
        )

    async def search(
        self,
        query: str,
        strategy: SearchStrategy = SearchStrategy.SEMANTIC,
        limit: int = 10,
    ) -> list[Article]:
        """
        Универсальный поиск с выбором стратегии.

        Args:
            query: Поисковый запрос
            strategy: Стратегия поиска
            limit: Максимальное количество результатов

        Returns:
            Список найденных статей

        Raises:
            ValueError: Если запрос пустой или стратегия недоступна
        """
        if not query or not query.strip():
            raise ValueError("Поисковый запрос не может быть пустым")

        query = query.strip()

        # Выбираем стратегию поиска
        if strategy == SearchStrategy.BY_NUMBER:
            # Точный поиск по номеру
            article = await self.search_by_number(query)
            return [article] if article else []

        elif strategy == SearchStrategy.FULLTEXT:
            # Полнотекстовый поиск
            return await self.search_by_text(query, limit=limit)

        elif strategy == SearchStrategy.SEMANTIC:
            # Семантический поиск
            if not self.vector_service:
                # Fallback на полнотекстовый поиск
                print(
                    "Векторный поиск недоступен, используется полнотекстовый"
                )
                return await self.search_by_text(query, limit=limit)

            return await self.semantic_search(query, top_k=limit)

        else:
            raise ValueError(f"Неизвестная стратегия поиска: {strategy}")

    async def get_all_articles(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Article]:
        """
        Получить все статьи (с пагинацией).

        Args:
            limit: Максимальное количество статей
            offset: Смещение для пагинации

        Returns:
            Список статей
        """
        return await self.repository.get_all(limit=limit, offset=offset)

    async def get_articles_by_chapter(
        self,
        chapter: str,
        limit: int = 50,
    ) -> list[Article]:
        """
        Получить статьи по главе ТК РФ.

        Args:
            chapter: Название главы
            limit: Максимальное количество результатов

        Returns:
            Список статей из главы
        """
        if not chapter or not chapter.strip():
            raise ValueError("Название главы не может быть пустым")

        # Используем полнотекстовый поиск для поиска по главе
        return await self.search_by_text(chapter.strip(), limit=limit)

    async def count_articles(self) -> int:
        """
        Получить общее количество статей в БД.

        Returns:
            Количество статей
        """
        return await self.repository.count()


class ArticleExplorerUseCase:
    """
    Use Case для исследования структуры ТК РФ.
    
    Помогает пользователям ориентироваться в структуре кодекса.
    """

    def __init__(self, article_repository: ArticleRepository):
        """
        Инициализация explorer use case.

        Args:
            article_repository: Репозиторий статей
        """
        self.repository = article_repository

    async def get_chapters_list(self) -> list[str]:
        """
        Получить список всех глав ТК РФ.

        Returns:
            Список уникальных названий глав
        """
        # Получаем все статьи
        articles = await self.repository.get_all(limit=1000)

        # Извлекаем уникальные главы
        chapters = {article.chapter for article in articles if article.chapter}

        return sorted(list(chapters))

    async def get_articles_range(
        self,
        start_number: str,
        end_number: str,
    ) -> list[Article]:
        """
        Получить диапазон статей.

        Args:
            start_number: Начальный номер
            end_number: Конечный номер

        Returns:
            Список статей в диапазоне
        """
        try:
            start = int(start_number)
            end = int(end_number)

            if start > end:
                start, end = end, start

            # Получаем все статьи и фильтруем по номеру
            all_articles = await self.repository.get_all(limit=1000)

            return [
                article
                for article in all_articles
                if article.number.isdigit()
                and start <= int(article.number) <= end
            ]

        except ValueError:
            raise ValueError("Номера статей должны быть числами")

    async def get_related_articles(
        self,
        article_number: str,
        context_size: int = 5,
    ) -> list[Article]:
        """
        Получить статьи, близкие по номеру.

        Args:
            article_number: Номер статьи
            context_size: Сколько статей взять до и после

        Returns:
            Список близких статей
        """
        try:
            number = int(article_number)
            start = max(1, number - context_size)
            end = number + context_size

            return await self.get_articles_range(str(start), str(end))

        except ValueError:
            raise ValueError("Номер статьи должен быть числом")
