"""API роуты для работы с вопросами."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import (
    get_db_session,
    get_conversation_orchestrator_use_case,
    get_quick_answer_use_case,
)
from src.api.schemas import (
    QuestionRequest,
    QuickQuestionRequest,
    LegalAnswerResponse,
    QuickAnswerResponse,
    ArticleResponse,
    AnswerMetadataResponse,
)
from src.application.use_cases.conversation_orchestrator import ConversationOrchestratorUseCase
from src.application.use_cases.quick_answer import QuickAnswerUseCase
from src.domain.entities import LegalQuery
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post(
    "",
    response_model=LegalAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Задать юридический вопрос",
    description="Отправить вопрос и получить ответ с сохранением истории диалога",
)
async def ask_question(
    request: QuestionRequest,
    session: AsyncSession = Depends(get_db_session),
    orchestrator: ConversationOrchestratorUseCase = Depends(get_conversation_orchestrator_use_case),
) -> LegalAnswerResponse:
    """
    Задать юридический вопрос с сохранением истории.
    
    Args:
        request: Запрос с вопросом и данными пользователя
        session: Сессия БД
        orchestrator: Use case для обработки вопроса
    
    Returns:
        LegalAnswerResponse: Ответ на вопрос с метаданными
    
    Raises:
        HTTPException: При ошибке обработки вопроса
    """
    try:
        logger.info(f"Получен вопрос от пользователя {request.user_id}")
        
        # Создаём доменную сущность запроса
        query = LegalQuery(
            question=request.question,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
        )
        
        # Обрабатываем вопрос через orchestrator
        answer = await orchestrator.handle_question(query)
        
        logger.info(f"Ответ сгенерирован для пользователя {request.user_id}, conversation_id={answer.conversation_id}")
        
        # Конвертируем в API response
        return LegalAnswerResponse(
            answer=answer.answer,
            articles=[
                ArticleResponse(
                    number=article.number,
                    title=article.title,
                    content=article.content,
                    chapter=article.chapter,
                    section=article.section,
                )
                for article in answer.context
            ],
            metadata=AnswerMetadataResponse(
                confidence=answer.confidence,
                sources_count=len(answer.context),
                article_numbers=answer.article_numbers,
                search_strategy="combined",
            ),
            conversation_id=str(answer.conversation_id) if answer.conversation_id else None,
        )
    
    except Exception as e:
        logger.error(f"Ошибка обработки вопроса: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обработке вопроса. Пожалуйста, попробуйте позже.",
        )


@router.post(
    "/quick",
    response_model=QuickAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Быстрый ответ на вопрос",
    description="Получить ответ на вопрос без сохранения истории диалога",
)
async def ask_quick_question(
    request: QuickQuestionRequest,
    session: AsyncSession = Depends(get_db_session),
    quick_answer_uc: QuickAnswerUseCase = Depends(get_quick_answer_use_case),
) -> QuickAnswerResponse:
    """
    Быстрый ответ на вопрос без сохранения истории.
    
    Args:
        request: Запрос с вопросом
        session: Сессия БД
        quick_answer_uc: Use case для быстрого ответа
    
    Returns:
        QuickAnswerResponse: Ответ на вопрос с метаданными
    
    Raises:
        HTTPException: При ошибке обработки вопроса
    """
    try:
        logger.info(f"Получен быстрый вопрос: {request.question[:50]}...")
        
        # Создаём доменную сущность запроса
        query = LegalQuery(
            question=request.question,
            user_id="anonymous",  # Для быстрых ответов нет user_id
        )
        
        # Получаем быстрый ответ
        answer = await quick_answer_uc.execute(query)
        
        logger.info(f"Быстрый ответ сгенерирован, статей: {len(answer.context)}")
        
        # Конвертируем в API response
        return QuickAnswerResponse(
            answer=answer.answer,
            articles=[
                ArticleResponse(
                    number=article.number,
                    title=article.title,
                    content=article.content,
                    chapter=article.chapter,
                    section=article.section,
                )
                for article in answer.context
            ],
            metadata=AnswerMetadataResponse(
                confidence=answer.confidence,
                sources_count=len(answer.context),
                article_numbers=answer.article_numbers,
                search_strategy="semantic",
            ),
        )
    
    except Exception as e:
        logger.error(f"Ошибка обработки быстрого вопроса: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обработке вопроса. Пожалуйста, попробуйте позже.",
        )
