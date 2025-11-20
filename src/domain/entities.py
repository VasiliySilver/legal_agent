"""
Доменные сущности юридического агента
"""
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Article(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    number: str = Field(min_length=1)
    title: str
    content: str = Field(min_length=1)
    chapter: str = ""


class LegalQuery(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=3, max_length=2000)
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_message(self):
        return {"role": "user", "content": self.text}


class LegalAnswer(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1)
    sources: List[Article] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_message(self):
        return {"role": "assistant", "content": self.text}


class LegalConversation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    user_id: str
    messages: List[Any] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    max_history: int = 10
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_query(self, query: LegalQuery):
        self.messages.append(query)
    
    def add_answer(self, answer: LegalAnswer):
        self.messages.append(answer)
    
    def get_context_for_llm(self):
        return [m.to_message() for m in self.messages if hasattr(m, 'to_message')]
