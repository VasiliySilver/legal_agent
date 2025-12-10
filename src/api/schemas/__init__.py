"""Экспорт всех API схем."""

from src.api.schemas.requests import (
    QuestionRequest,
    QuickQuestionRequest,
    CreateConversationRequest,
    SearchArticlesRequest,
    UpdateConversationRequest,
    SearchStrategyEnum,
)

from src.api.schemas.responses import (
    ArticleResponse,
    MessageResponse,
    ConversationResponse,
    ConversationDetailResponse,
    AnswerMetadataResponse,
    LegalAnswerResponse,
    QuickAnswerResponse,
    ConversationListResponse,
    SearchArticlesResponse,
    HealthCheckResponse,
    ErrorResponse,
    MessageCreatedResponse,
)

__all__ = [
    # Requests
    "QuestionRequest",
    "QuickQuestionRequest",
    "CreateConversationRequest",
    "SearchArticlesRequest",
    "UpdateConversationRequest",
    "SearchStrategyEnum",
    # Responses
    "ArticleResponse",
    "MessageResponse",
    "ConversationResponse",
    "ConversationDetailResponse",
    "AnswerMetadataResponse",
    "LegalAnswerResponse",
    "QuickAnswerResponse",
    "ConversationListResponse",
    "SearchArticlesResponse",
    "HealthCheckResponse",
    "ErrorResponse",
    "MessageCreatedResponse",
]
