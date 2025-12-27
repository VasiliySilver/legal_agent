"""
Dependency Injection контейнер для FastAPI.

Предоставляет зависимости для роутов:
- Репозитории (ArticleRepository, ConversationRepository)
- Сервисы (LLMService, VectorService)
- Use Cases (AnswerLegalQuestionUseCase, ManageConversationUseCase и др.)
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_async_session
from src.infrastructure.repositories import ArticleRepository, ConversationRepository
from src.application.services.llm_service import LLMService
from src.application.services.vector_service import VectorService
from src.application.use_cases.answer_legal_question import AnswerLegalQuestionUseCase
from src.application.use_cases.manage_conversation import ManageConversationUseCase
from src.application.use_cases.search_articles import SearchArticlesUseCase
from src.application.use_cases.conversation_orchestrator import (
    ConversationOrchestratorUseCase,
)
from src.application.use_cases.quick_answer import QuickAnswerUseCase
from src.application.use_cases.multi_strategy_search import MultiStrategySearchUseCase
import os


# === Database Session ===


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить асинхронную сессию БД."""
    async for session in get_async_session():
        yield session


# === Repositories ===


async def get_article_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ArticleRepository:
    """Получить репозиторий статей."""
    return ArticleRepository(session)


async def get_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationRepository:
    """Получить репозиторий диалогов."""
    return ConversationRepository(session)


# === Services ===


def get_llm_service() -> LLMService:
    """Получить сервис LLM."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY не установлен в переменных окружения")

    # Поддержка прокси для Groq API
    proxy = os.getenv("GROQ_PROXY")
    return LLMService(api_key=api_key, proxy=proxy)


def get_vector_service() -> VectorService:
    """Получить сервис векторного поиска."""
    # По умолчанию используем FAISS для быстрой работы
    # В production можно переключить на PostgresVectorStore
    from src.application.services.vector_service import VectorBackend

    model_name = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    backend = VectorBackend.FAISS
    return VectorService(backend=backend, model_name=model_name)


# === Use Cases ===


async def get_multi_strategy_search_use_case(
    session: AsyncSession = Depends(get_db_session),
    vector_service: VectorService = Depends(get_vector_service),
) -> MultiStrategySearchUseCase:
    """Получить use case для комбинированного поиска."""
    article_repo = ArticleRepository(session)

    return MultiStrategySearchUseCase(
        article_repository=article_repo, vector_service=vector_service
    )


async def get_answer_legal_question_use_case(
    session: AsyncSession = Depends(get_db_session),
    llm_service: LLMService = Depends(get_llm_service),
    multi_strategy_search: MultiStrategySearchUseCase = Depends(
        get_multi_strategy_search_use_case
    ),
) -> AnswerLegalQuestionUseCase:
    """Получить use case для ответа на юридические вопросы."""
    conversation_repo = ConversationRepository(session)

    return AnswerLegalQuestionUseCase(
        multi_strategy_search=multi_strategy_search,
        conversation_repository=conversation_repo,
        llm_service=llm_service,
    )


async def get_manage_conversation_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> ManageConversationUseCase:
    """Получить use case для управления диалогами."""
    conversation_repo = ConversationRepository(session)
    return ManageConversationUseCase(conversation_repository=conversation_repo)


async def get_search_articles_use_case(
    session: AsyncSession = Depends(get_db_session),
    vector_service: VectorService = Depends(get_vector_service),
) -> SearchArticlesUseCase:
    """Получить use case для поиска статей."""
    article_repo = ArticleRepository(session)
    return SearchArticlesUseCase(
        article_repository=article_repo, vector_service=vector_service
    )


async def get_conversation_orchestrator_use_case(
    answer_use_case: AnswerLegalQuestionUseCase = Depends(
        get_answer_legal_question_use_case
    ),
    manage_use_case: ManageConversationUseCase = Depends(
        get_manage_conversation_use_case
    ),
) -> ConversationOrchestratorUseCase:
    """Получить orchestrator для полного цикла вопрос-ответ."""
    return ConversationOrchestratorUseCase(
        answer_use_case=answer_use_case, manage_conversation_use_case=manage_use_case
    )


async def get_quick_answer_use_case(
    session: AsyncSession = Depends(get_db_session),
    llm_service: LLMService = Depends(get_llm_service),
    vector_service: VectorService = Depends(get_vector_service),
) -> QuickAnswerUseCase:
    """Получить use case для быстрых ответов без истории."""
    article_repo = ArticleRepository(session)

    return QuickAnswerUseCase(
        article_repository=article_repo,
        llm_service=llm_service,
        vector_service=vector_service,
    )
