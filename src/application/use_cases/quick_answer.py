from typing import Optional
from src.application.services.llm_service import LLMService
from src.application.services.vector_service import VectorService
from src.application.use_cases.answer_legal_question import AnswerLegalQuestionUseCase
from src.domain.entities import LegalAnswer, LegalQuery
from src.infrastructure.repositories import ArticleRepository


class QuickAnswerUseCase:
    """
    Упрощённый Use Case для быстрого ответа без сохранения в БД.

    Используется для разовых вопросов без контекста диалога.
    """

    def __init__(
        self,
        article_repository: ArticleRepository,
        llm_service: LLMService,
        vector_service: Optional[VectorService] = None,
    ):
        """
        Инициализация упрощённого use case.

        Args:
            article_repository: Репозиторий статей
            llm_service: Сервис LLM
            vector_service: Векторный поиск (опционально)
        """
        self.article_repository = article_repository
        self.llm_service = llm_service
        self.vector_service = vector_service

    async def execute(self, question: LegalQuery | str, top_k: int = 5) -> LegalAnswer:
        """
        Быстрый ответ на вопрос.

        Args:
            question: Вопрос пользователя (строка или LegalQuery объект)
            top_k: Количество статей для поиска

        Returns:
            LegalAnswer: Ответ с источниками

        Raises:
            ValueError: Если вопрос пустой
        """
        # Если передан LegalQuery, извлекаем из него вопрос
        if isinstance(question, LegalQuery):
            query = question
            question_text = question.question
        else:
            # Если строка - создаём LegalQuery
            if not question or not question.strip():
                raise ValueError("Вопрос не может быть пустым")
            question_text = question.strip()
            query = LegalQuery(question=question_text, user_id="anonymous")

        # Используем основной use case без conversation_id
        main_use_case = AnswerLegalQuestionUseCase(
            article_repository=self.article_repository,
            llm_service=self.llm_service,
            vector_service=self.vector_service,
        )

        return await main_use_case.execute(query, conversation_id=None, top_k=top_k)
