"""
Инфраструктура: ORM модели для PostgreSQL
SQLAlchemy модели для хранения данных юридического агента
"""

from datetime import datetime
from typing import List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Float,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.infrastructure.database import Base
from src.domain.entities import Article, LegalQuery, LegalAnswer, LegalConversation, ArticleStatus


# ============================================================================
# ARTICLE MODEL (СТАТЬЯ ТК РФ)
# ============================================================================

class ArticleModel(Base):
    """
    ORM модель для статьи Трудового кодекса РФ
    
    Таблица: articles
    """
    __tablename__ = "articles"
    
    # Первичный ключ
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Номер статьи (уникальный)
    number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    
    # Название статьи
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Полный текст статьи
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Иерархическая структура ТК РФ
    part: Mapped[str] = mapped_column(String(100), nullable=True)
    section: Mapped[str] = mapped_column(String(200), nullable=True)
    chapter: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Характеристики статьи
    text_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        SQLEnum(ArticleStatus, name='article_status', create_constraint=True),
        nullable=False,
        default=ArticleStatus.ACTIVE
    )
    
    # Метаинформация источника
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Метаданные (для расширения)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True, default={})
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Индексы для полнотекстового поиска
    __table_args__ = (
        # GIN индекс для быстрого полнотекстового поиска (PostgreSQL)
        Index('ix_articles_content_gin', 'content', postgresql_using='gin', postgresql_ops={'content': 'gin_trgm_ops'}),
        Index('ix_articles_title_gin', 'title', postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
    )
    
    def to_entity(self) -> Article:
        """
        Преобразовать ORM модель в доменную сущность
        
        Returns:
            Article: Доменная сущность статьи
        """
        return Article(
            number=self.number,
            title=self.title,
            content=self.content,
            part=self.part,
            section=self.section,
            chapter=self.chapter or "",
            text_length=self.text_length,
            status=ArticleStatus(self.status) if isinstance(self.status, str) else self.status,
            source=self.source,
            source_url=self.source_url,
            fetched_at=self.fetched_at,
        )
    
    @staticmethod
    def from_entity(entity: Article) -> "ArticleModel":
        """
        Создать ORM модель из доменной сущности
        
        Args:
            entity: Доменная сущность статьи
            
        Returns:
            ArticleModel: ORM модель
        """
        return ArticleModel(
            number=entity.number,
            title=entity.title,
            content=entity.content,
            part=entity.part,
            section=entity.section,
            chapter=entity.chapter,
            text_length=entity.text_length,
            status=entity.status,
            source=entity.source,
            source_url=entity.source_url,
            fetched_at=entity.fetched_at,
        )
    
    def __repr__(self) -> str:
        return f"<ArticleModel(id={self.id}, number={self.number}, title={self.title[:30]}...)>"


# ============================================================================
# CONVERSATION MODEL (ДИАЛОГ)
# ============================================================================

class ConversationModel(Base):
    """
    ORM модель для диалога с пользователем
    
    Таблица: conversations
    """
    __tablename__ = "conversations"
    
    # Первичный ключ
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # ID пользователя (из Telegram, веб-интерфейса и т.д.)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Название диалога
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Метаданные (настройки, контекст)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True, default={})
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Связь one-to-many с сообщениями
    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",  # Загружать сообщения сразу
        order_by="MessageModel.created_at",
    )
    
    def to_entity(self) -> LegalConversation:
        """
        Преобразовать ORM модель в доменную сущность
        
        Returns:
            LegalConversation: Доменная сущность диалога
        """
        conversation = LegalConversation(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            started_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata_json or {},
        )
        
        # Добавляем сообщения
        for msg_model in self.messages:
            msg_entity = msg_model.to_entity()
            conversation.messages.append(msg_entity)
        
        return conversation
    
    @staticmethod
    def from_entity(entity: LegalConversation) -> "ConversationModel":
        """
        Создать ORM модель из доменной сущности
        
        Args:
            entity: Доменная сущность диалога
            
        Returns:
            ConversationModel: ORM модель
        """
        return ConversationModel(
            user_id=entity.user_id,
            title=entity.title,
            metadata_json=entity.metadata,
            created_at=entity.started_at,
            updated_at=entity.updated_at,
        )
    
    def __repr__(self) -> str:
        return f"<ConversationModel(id={self.id}, user_id={self.user_id}, messages={len(self.messages)})>"


# ============================================================================
# MESSAGE MODEL (СООБЩЕНИЕ В ДИАЛОГЕ)
# ============================================================================

class MessageModel(Base):
    """
    ORM модель для сообщения в диалоге
    
    Таблица: messages
    """
    __tablename__ = "messages"
    
    # Первичный ключ
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Внешний ключ на диалог
    conversation_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Роль (user, assistant, system)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Контент сообщения
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Уверенность (для ответов агента)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Источники (статьи ТК РФ, использованные для ответа)
    sources: Mapped[list] = mapped_column(JSON, nullable=True, default=[])
    
    # Метаданные
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True, default={})
    
    # Временная метка
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Связь many-to-one с диалогом
    conversation: Mapped["ConversationModel"] = relationship(
        "ConversationModel",
        back_populates="messages",
    )
    
    def to_entity(self):
        """
        Преобразовать ORM модель в доменную сущность
        
        Returns:
            Union[LegalQuery, LegalAnswer]: Доменная сущность
        """
        if self.role == "user":
            return LegalQuery(
                question=self.content,
                user_id=self.conversation.user_id,
                timestamp=self.created_at,
                metadata=self.metadata_json or {},
            )
        elif self.role == "assistant":
            # Преобразуем sources из JSON в список Article
            sources = []
            if self.sources:
                for source_data in self.sources:
                    if isinstance(source_data, dict):
                        article = Article(
                            number=source_data.get("number", ""),
                            title=source_data.get("title", ""),
                            content=source_data.get("content", ""),
                            chapter=source_data.get("chapter", ""),
                        )
                        sources.append(article)
            
            return LegalAnswer(
                answer=self.content,
                sources=sources,
                confidence=self.confidence or 0.0,
                timestamp=self.created_at,
                metadata=self.metadata_json or {},
            )
        else:
            raise ValueError(f"Неизвестная роль сообщения: {self.role}")
    
    @staticmethod
    def from_query(query: LegalQuery, conversation_id: int) -> "MessageModel":
        """
        Создать ORM модель из запроса пользователя
        
        Args:
            query: Доменная сущность запроса
            conversation_id: ID диалога
            
        Returns:
            MessageModel: ORM модель
        """
        return MessageModel(
            conversation_id=conversation_id,
            role="user",
            content=query.question,  # Используем question, а не text
            metadata_json=query.metadata,
            created_at=query.timestamp,
        )
    
    @staticmethod
    def from_answer(answer: LegalAnswer, conversation_id: int) -> "MessageModel":
        """
        Создать ORM модель из ответа агента
        
        Args:
            answer: Доменная сущность ответа
            conversation_id: ID диалога
            
        Returns:
            MessageModel: ORM модель
        """
        # Преобразуем context (статьи) в JSON
        sources_json = []
        for article in answer.context:
            sources_json.append({
                "number": article.number,
                "title": article.title,
                "content": article.content,
                "chapter": article.chapter,
            })
        
        return MessageModel(
            conversation_id=conversation_id,
            role="assistant",
            content=answer.answer,  # Используем answer, а не text
            confidence=answer.confidence,
            sources=sources_json,
            metadata_json=answer.metadata,
            created_at=answer.timestamp,
        )
    
    def __repr__(self) -> str:
        preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<MessageModel(id={self.id}, role={self.role}, content={preview})>"
