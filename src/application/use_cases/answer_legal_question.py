"""
Use Case: Ответ на юридический вопрос.

Оркестрирует процесс поиска релевантных статей ТК РФ
и генерации ответа с помощью LLM.
"""

from typing import Optional

from src.domain.entities import Article, LegalAnswer, LegalQuery, Message
from src.application.services.llm_service import LLMService
from src.application.services.vector_service import VectorService
from src.infrastructure.repositories import ArticleRepository, ConversationRepository


class AnswerLegalQuestionUseCase:
    """
    Use Case для ответа на юридические вопросы пользователей.

    Алгоритм:
    1. Получить вопрос пользователя (LegalQuery)
    2. Найти релевантные статьи:
       - Сначала векторный поиск (семантический)
       - Затем полнотекстовый поиск (если нужно)
    3. Получить историю диалога (если есть conversation_id)
    4. Отправить контекст в LLM для генерации ответа
    5. Вернуть ответ с источниками (LegalAnswer)
    """

    def __init__(
        self,
        article_repository: ArticleRepository,
        llm_service: LLMService,
        vector_service: Optional[VectorService] = None,
        conversation_repository: Optional[ConversationRepository] = None,
    ):
        """
        Инициализация use case.

        Args:
            article_repository: Репозиторий для работы со статьями
            llm_service: Сервис для генерации ответов
            vector_service: Сервис векторного поиска (опционально)
            conversation_repository: Репозиторий диалогов (опционально)
        """
        self.article_repository = article_repository
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.conversation_repository = conversation_repository

    async def execute(
        self,
        query: LegalQuery,
        conversation_id: Optional[int] = None,
        top_k: int = 5,
    ) -> LegalAnswer:
        """
        Выполнить use case: ответить на юридический вопрос.

        Args:
            query: Запрос пользователя
            conversation_id: ID диалога для контекста (опционально)
            top_k: Количество статей для поиска

        Returns:
            LegalAnswer: Ответ с источниками и уверенностью

        Raises:
            ValueError: Если вопрос пустой
        """
        if not query.question or not query.question.strip():
            raise ValueError("Вопрос не может быть пустым")

        # Шаг 1: Найти релевантные статьи
        articles = await self._find_relevant_articles(query.question, top_k)

        # Шаг 2: Получить историю диалога (если есть)
        history = None
        if conversation_id and self.conversation_repository:
            history = await self._get_conversation_history(conversation_id)

        # Шаг 3: Сгенерировать ответ через LLM
        answer = await self.llm_service.generate_answer(
            question=query.question,
            articles=articles,
            history=history,
        )

        return answer

    async def _find_relevant_articles(self, question: str, top_k: int) -> list[Article]:
        """
        Найти релевантные статьи для вопроса.

        Стратегия поиска:
        1. Если есть vector_service - используем семантический поиск
        2. Иначе - используем полнотекстовый поиск в БД

        Args:
            question: Вопрос пользователя
            top_k: Количество статей

        Returns:
            Список релевантных статей
        """
        # Попытка семантического поиска
        if self.vector_service:
            try:
                articles = await self.vector_service.find_similar(
                    query=question,
                    top_k=top_k,
                )
                if articles:
                    return articles
            except Exception as e:
                # Логируем ошибку, но продолжаем с полнотекстовым поиском
                print(f"Ошибка векторного поиска: {e}")

        # Fallback: полнотекстовый поиск в БД
        articles = await self.article_repository.search(
            query=question,
            limit=top_k,
        )

        return articles

    async def _get_conversation_history(
        self, conversation_id: int
    ) -> Optional[list[Message]]:
        """
        Получить историю диалога.

        Args:
            conversation_id: ID диалога

        Returns:
            Список сообщений или None
        """
        if not self.conversation_repository:
            return None

        try:
            conversation = await self.conversation_repository.get_by_id(conversation_id)
            if conversation:
                return conversation.messages
        except Exception as e:
            print(f"Ошибка получения истории диалога: {e}")

        return None
