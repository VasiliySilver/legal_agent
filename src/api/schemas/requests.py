"""Pydantic схемы для валидации запросов API."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class SearchStrategyEnum(str, Enum):
    """Стратегия поиска статей."""
    BY_NUMBER = "by_number"
    FULLTEXT = "fulltext"
    SEMANTIC = "semantic"


class QuestionRequest(BaseModel):
    """Запрос на задавание вопроса с сохранением истории."""
    
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Текст юридического вопроса"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Идентификатор пользователя"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="ID существующего диалога (если None - создаётся новый)"
    )
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Валидация вопроса."""
        if not v.strip():
            raise ValueError("Вопрос не может быть пустым")
        return v.strip()
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Валидация user_id."""
        if not v.strip():
            raise ValueError("user_id не может быть пустым")
        return v.strip()


class QuickQuestionRequest(BaseModel):
    """Запрос на быстрый ответ без сохранения истории."""
    
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Текст юридического вопроса"
    )
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Валидация вопроса."""
        if not v.strip():
            raise ValueError("Вопрос не может быть пустым")
        return v.strip()


class CreateConversationRequest(BaseModel):
    """Запрос на создание нового диалога."""
    
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Идентификатор пользователя"
    )
    title: Optional[str] = Field(
        None,
        max_length=500,
        description="Название диалога (опционально)"
    )
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Валидация user_id."""
        if not v.strip():
            raise ValueError("user_id не может быть пустым")
        return v.strip()
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Валидация title."""
        if v is not None:
            return v.strip() or None
        return None


class SearchArticlesRequest(BaseModel):
    """Запрос на поиск статей."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Поисковый запрос (номер статьи или текст)"
    )
    strategy: SearchStrategyEnum = Field(
        SearchStrategyEnum.SEMANTIC,
        description="Стратегия поиска"
    )
    limit: int = Field(
        5,
        ge=1,
        le=50,
        description="Количество результатов"
    )
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Валидация запроса."""
        if not v.strip():
            raise ValueError("Поисковый запрос не может быть пустым")
        return v.strip()


class UpdateConversationRequest(BaseModel):
    """Запрос на обновление диалога."""
    
    title: Optional[str] = Field(
        None,
        max_length=500,
        description="Новое название диалога"
    )
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Валидация title."""
        if v is not None:
            return v.strip() or None
        return None
