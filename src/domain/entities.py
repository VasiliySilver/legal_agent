"""
Доменные сущности юридического агента
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Article(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    id: Optional[UUID] = Field(default_factory=uuid4)
    number: str = Field(min_length=1)
    title: str
    content: str = Field(min_length=1)
    chapter: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LegalQuery(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=3, max_length=2000)
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[int | UUID] = None  # Может быть int (из БД) или UUID (в памяти)
    
    # Сохраняем старое поле text для совместимости
    @property
    def text(self) -> str:
        return self.question
    
    def to_message(self):
        return {"role": "user", "content": self.question}


class LegalAnswer(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    answer: str = Field(min_length=1)
    sources: List[int] = Field(default_factory=list)  # Номера статей
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Сохраняем старое поле text для совместимости
    @property
    def text(self) -> str:
        return self.answer
    
    def to_message(self):
        return {"role": "assistant", "content": self.answer}


class Message(BaseModel):
    """Сообщение в диалоге (универсальный класс)."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID = Field(default_factory=uuid4)
    conversation_id: Optional[int | UUID] = None  # Может быть int (из БД) или UUID (в памяти)
    role: str  # "user" или "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sources: Optional[List[int]] = Field(default_factory=list)  # Для ответов ассистента
    confidence: Optional[float] = None  # Для ответов ассистента
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LegalConversation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: Optional[int | UUID] = Field(default_factory=uuid4)  # int из БД или UUID в памяти
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    max_history: int = 10
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Для совместимости со старым именем
    @property
    def created_at(self) -> datetime:
        return self.started_at
    
    def add_query(self, query: LegalQuery):
        self.messages.append(query)
    
    def add_answer(self, answer: LegalAnswer):
        self.messages.append(answer)
    
    def get_context_for_llm(self):
        return [m.to_message() for m in self.messages if hasattr(m, 'to_message')]
