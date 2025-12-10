"""Pydantic схемы для форматирования ответов API."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ArticleResponse(BaseModel):
    """Схема ответа для статьи ТК РФ."""

    model_config = ConfigDict(from_attributes=True)

    number: str = Field(..., description="Номер статьи (например, '80')")
    title: str = Field(..., description="Название статьи")
    content: str = Field(..., description="Полный текст статьи")
    chapter: Optional[str] = Field(None, description="Глава ТК РФ")
    section: Optional[str] = Field(None, description="Раздел ТК РФ")


class MessageResponse(BaseModel):
    """Схема ответа для сообщения в диалоге."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID сообщения")
    role: str = Field(..., description="Роль отправителя (user/assistant)")
    content: str = Field(..., description="Текст сообщения")
    timestamp: datetime = Field(..., description="Время создания")


class ConversationResponse(BaseModel):
    """Схема ответа для диалога."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID диалога")
    user_id: str = Field(..., description="ID пользователя")
    title: Optional[str] = Field(None, description="Название диалога")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата последнего обновления")
    message_count: int = Field(0, description="Количество сообщений в диалоге")


class ConversationDetailResponse(ConversationResponse):
    """Схема ответа для детального диалога с историей."""

    messages: List[MessageResponse] = Field(
        default_factory=list, description="История сообщений"
    )


class AnswerMetadataResponse(BaseModel):
    """Схема ответа для метаданных ответа."""

    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Уверенность в ответе (0-1)"
    )
    sources_count: int = Field(..., description="Количество использованных статей")
    article_numbers: List[str] = Field(
        default_factory=list, description="Номера статей, упомянутых в ответе"
    )
    search_strategy: Optional[str] = Field(None, description="Стратегия поиска")


class LegalAnswerResponse(BaseModel):
    """Схема ответа на юридический вопрос."""

    model_config = ConfigDict(from_attributes=True)

    answer: str = Field(..., description="Текст ответа на вопрос")
    articles: List[ArticleResponse] = Field(
        default_factory=list, description="Статьи ТК РФ, использованные для ответа"
    )
    metadata: AnswerMetadataResponse = Field(..., description="Метаданные ответа")
    conversation_id: Optional[str] = Field(None, description="ID диалога (если есть)")


class QuickAnswerResponse(BaseModel):
    """Схема ответа для быстрого вопроса без истории."""

    answer: str = Field(..., description="Текст ответа на вопрос")
    articles: List[ArticleResponse] = Field(
        default_factory=list, description="Статьи ТК РФ, использованные для ответа"
    )
    metadata: AnswerMetadataResponse = Field(..., description="Метаданные ответа")


class ConversationListResponse(BaseModel):
    """Схема ответа для списка диалогов."""

    conversations: List[ConversationResponse] = Field(
        default_factory=list, description="Список диалогов пользователя"
    )
    total: int = Field(..., description="Общее количество диалогов")


class SearchArticlesResponse(BaseModel):
    """Схема ответа для поиска статей."""

    articles: List[ArticleResponse] = Field(
        default_factory=list, description="Найденные статьи"
    )
    total: int = Field(..., description="Количество найденных статей")
    strategy: str = Field(..., description="Использованная стратегия поиска")


class HealthCheckResponse(BaseModel):
    """Схема ответа для healthcheck."""

    status: str = Field(..., description="Статус приложения")
    database: str = Field(..., description="Статус подключения к БД")
    timestamp: datetime = Field(..., description="Время проверки")


class ErrorResponse(BaseModel):
    """Схема ответа для ошибок."""

    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    details: Optional[dict] = Field(None, description="Дополнительные детали")


class MessageCreatedResponse(BaseModel):
    """Схема ответа при создании сообщения."""

    message: MessageResponse = Field(..., description="Созданное сообщение")
    conversation_id: str = Field(..., description="ID диалога")
