"""API роуты для работы с диалогами."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import (
    get_db_session,
    get_manage_conversation_use_case,
)
from src.api.schemas import (
    CreateConversationRequest,
    UpdateConversationRequest,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageResponse,
)
from src.application.use_cases.manage_conversation import ManageConversationUseCase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить список диалогов пользователя",
    description="Возвращает все диалоги указанного пользователя",
)
async def get_conversations(
    user_id: str = Query(..., description="ID пользователя"),
    session: AsyncSession = Depends(get_db_session),
    manage_uc: ManageConversationUseCase = Depends(get_manage_conversation_use_case),
) -> ConversationListResponse:
    """
    Получить список диалогов пользователя.

    Args:
        user_id: ID пользователя
        session: Сессия БД
        manage_uc: Use case для управления диалогами

    Returns:
        ConversationListResponse: Список диалогов
    """
    try:
        logger.info(f"Запрос списка диалогов для пользователя {user_id}")

        conversations = await manage_uc.get_user_conversations(user_id)

        logger.info(f"Найдено {len(conversations)} диалогов для пользователя {user_id}")

        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    id=str(conv.id),
                    user_id=conv.user_id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    message_count=len(conv.messages),
                )
                for conv in conversations
            ],
            total=len(conversations),
        )

    except Exception as e:
        logger.error(f"Ошибка получения списка диалогов: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка диалогов",
        )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый диалог",
    description="Создать пустой диалог для пользователя",
)
async def create_conversation(
    request: CreateConversationRequest,
    session: AsyncSession = Depends(get_db_session),
    manage_uc: ManageConversationUseCase = Depends(get_manage_conversation_use_case),
) -> ConversationResponse:
    """
    Создать новый диалог.

    Args:
        request: Запрос с данными пользователя
        session: Сессия БД
        manage_uc: Use case для управления диалогами

    Returns:
        ConversationResponse: Созданный диалог
    """
    try:
        logger.info(f"Создание нового диалога для пользователя {request.user_id}")

        conversation = await manage_uc.create_conversation(
            user_id=request.user_id,
            title=request.title,
        )

        logger.info(f"Диалог создан: {conversation.id}")

        return ConversationResponse(
            id=str(conversation.id),
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0,
        )

    except Exception as e:
        logger.error(f"Ошибка создания диалога: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании диалога",
        )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить диалог с историей",
    description="Возвращает диалог со всеми сообщениями",
)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db_session),
    manage_uc: ManageConversationUseCase = Depends(get_manage_conversation_use_case),
) -> ConversationDetailResponse:
    """
    Получить диалог с историей сообщений.

    Args:
        conversation_id: ID диалога
        session: Сессия БД
        manage_uc: Use case для управления диалогами

    Returns:
        ConversationDetailResponse: Диалог с историей

    Raises:
        HTTPException: Если диалог не найден
    """
    try:
        logger.info(f"Запрос диалога {conversation_id}")

        # Преобразуем conversation_id в int
        try:
            conv_id = int(conversation_id)
        except ValueError:
            # Возвращаем 404 для невалидного ID (ресурс не найден)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Диалог {conversation_id} не найден",
            )

        try:
            conversation = await manage_uc.get_conversation(conv_id)
        except ValueError as e:
            # Use case выбрасывает ValueError, если диалог не найден
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

        logger.info(
            f"Диалог найден: {conversation_id}, сообщений: {len(conversation.messages)}"
        )

        return ConversationDetailResponse(
            id=str(conversation.id),
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages),
            messages=[
                MessageResponse(
                    id=str(msg.id),
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp,
                )
                for msg in conversation.messages
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения диалога: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении диалога",
        )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить диалог",
    description="Удаляет диалог со всеми сообщениями",
)
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db_session),
    manage_uc: ManageConversationUseCase = Depends(get_manage_conversation_use_case),
):
    """
    Удалить диалог.

    Args:
        conversation_id: ID диалога
        session: Сессия БД
        manage_uc: Use case для управления диалогами

    Raises:
        HTTPException: Если диалог не найден
    """
    try:
        logger.info(f"Удаление диалога {conversation_id}")

        # Преобразуем conversation_id в int
        try:
            conv_id = int(conversation_id)
        except ValueError:
            # Возвращаем 404 для невалидного ID (ресурс не найден)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Диалог {conversation_id} не найден",
            )

        deleted = await manage_uc.delete_conversation(conv_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Диалог {conversation_id} не найден",
            )

        logger.info(f"Диалог удалён: {conversation_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления диалога: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении диалога",
        )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить диалог",
    description="Обновить название диалога",
)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    session: AsyncSession = Depends(get_db_session),
    manage_uc: ManageConversationUseCase = Depends(get_manage_conversation_use_case),
) -> ConversationResponse:
    """
    Обновить диалог (пока только название).

    Args:
        conversation_id: ID диалога
        request: Данные для обновления
        session: Сессия БД
        manage_uc: Use case для управления диалогами

    Returns:
        ConversationResponse: Обновлённый диалог

    Raises:
        HTTPException: Если диалог не найден
    """
    try:
        logger.info(f"Обновление диалога {conversation_id}")

        # Преобразуем conversation_id в int
        try:
            conv_id = int(conversation_id)
        except ValueError:
            # Возвращаем 404 для невалидного ID (ресурс не найден)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Диалог {conversation_id} не найден",
            )

        # Обновляем диалог
        conversation = await manage_uc.update_conversation(
            conversation_id=conv_id,
            title=request.title,
        )

        logger.info(f"Диалог обновлён: {conversation_id}")

        return ConversationResponse(
            id=str(conversation.id),
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages),
        )

    except ValueError as e:
        logger.warning(f"Диалог не найден: {conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления диалога: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении диалога",
        )
