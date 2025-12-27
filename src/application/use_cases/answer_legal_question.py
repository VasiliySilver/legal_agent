"""
Use Case: Ответ на юридический вопрос.

Оркестрирует процесс поиска релевантных статей ТК РФ
и генерации ответа с помощью LLM.
"""

from typing import Optional

from src.domain.entities import LegalAnswer, LegalQuery, Message
from src.application.services.llm_service import LLMService
from src.application.use_cases.multi_strategy_search import MultiStrategySearchUseCase
from src.infrastructure.repositories import ConversationRepository


class AnswerLegalQuestionUseCase:
    """
    Use Case для ответа на юридические вопросы пользователей.

    Алгоритм:
    1. Получить вопрос пользователя (LegalQuery)
    2. Найти релевантные статьи через MultiStrategySearchUseCase:
       - Проверка на номер статьи
       - Семантический поиск (векторная БД)
       - Fallback на полнотекстовый поиск (PostgreSQL)
    3. Получить историю диалога (если есть conversation_id)
    4. Отправить контекст в LLM для генерации ответа
    5. Вернуть ответ с источниками (LegalAnswer)
    """

    def __init__(
        self,
        multi_strategy_search: MultiStrategySearchUseCase,
        llm_service: LLMService,
        conversation_repository: Optional[ConversationRepository] = None,
    ):
        """
        Инициализация use case.

        Args:
            multi_strategy_search: Мульти-стратегический поиск статей
            llm_service: Сервис для генерации ответов
            conversation_repository: Репозиторий диалогов (опционально)
        """
        self.multi_strategy_search = multi_strategy_search
        self.llm_service = llm_service
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

        # Шаг 1: Найти релевантные статьи через мульти-стратегический поиск
        articles = await self.multi_strategy_search.search(
            query.question, min_results=1, max_results=top_k
        )

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
