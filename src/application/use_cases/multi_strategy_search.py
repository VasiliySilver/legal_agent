from typing import Optional
from src.application.services.vector_service import VectorService
from src.application.use_cases.search_articles import SearchArticlesUseCase
from src.domain.entities import Article
from src.infrastructure.repositories import ArticleRepository


class MultiStrategySearchUseCase:
    """
    Use Case с автоматическим выбором лучшей стратегии поиска.

    Пытается применить разные стратегии последовательно,
    пока не найдёт результаты.
    """

    def __init__(
        self,
        article_repository: ArticleRepository,
        vector_service: Optional[VectorService] = None,
    ):
        """
        Инициализация мульти-стратегического поиска.

        Args:
            article_repository: Репозиторий статей
            vector_service: Векторный сервис (опционально)
        """
        self.search_use_case = SearchArticlesUseCase(
            article_repository=article_repository,
            vector_service=vector_service,
        )

    async def search(
        self,
        query: str,
        min_results: int = 3,
        max_results: int = 10,
    ) -> list[Article]:
        """
        Умный поиск с автоматическим выбором стратегии.

        Алгоритм:
        1. Проверяем, является ли запрос номером статьи
        2. Пытаемся семантический поиск (если доступен)
        3. Fallback на полнотекстовый поиск

        Args:
            query: Поисковый запрос
            min_results: Минимальное количество результатов
            max_results: Максимальное количество результатов

        Returns:
            Список найденных статей
        """
        if not query or not query.strip():
            raise ValueError("Поисковый запрос не может быть пустым")

        query = query.strip()

        # Стратегия 1: Если запрос похож на номер статьи
        if self._looks_like_article_number(query):
            article = await self.search_use_case.search_by_number(query)
            if article:
                return [article]

        # Стратегия 2: Семантический поиск (если доступен)
        if self.search_use_case.vector_service:
            try:
                results = await self.search_use_case.semantic_search(
                    query, top_k=max_results
                )
                if len(results) >= min_results:
                    return results
            except Exception as e:
                print(f"Ошибка семантического поиска: {e}")

        # Стратегия 3: Полнотекстовый поиск (fallback)
        results = await self.search_use_case.search_by_text(
            query, limit=max_results
        )

        return results

    def _looks_like_article_number(self, query: str) -> bool:
        """
        Проверяет, похож ли запрос на номер статьи.

        Args:
            query: Поисковый запрос

        Returns:
            True, если похоже на номер статьи
        """
        # Удаляем слово "статья" если есть
        query_clean = query.lower().replace("статья", "").strip()

        # Проверяем, является ли число или число с буквой
        # Например: "80", "77", "139.1"
        if query_clean.replace(".", "").isdigit():
            return True

        return False