"""
Инфраструктура: Репозитории для работы с базой данных
Паттерн Repository: изоляция бизнес-логики от деталей работы с БД
Все операции асинхронные (async/await)
"""

from typing import List, Optional
from sqlalchemy import select, update, delete, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities import Article, LegalConversation, LegalQuery, LegalAnswer
from src.infrastructure.models import ArticleModel, ConversationModel, MessageModel


# ============================================================================
# ARTICLE REPOSITORY
# ============================================================================

class ArticleRepository:
    """
    Репозиторий для работы со статьями ТК РФ
    
    Операции:
    - Создание статьи
    - Получение статьи по номеру
    - Получение всех статей
    - Поиск статей (полнотекстовый)
    - Обновление статьи
    - Удаление статьи
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, article: Article) -> Article:
        """
        Создать новую статью в БД
        
        Args:
            article: Доменная сущность статьи
            
        Returns:
            Article: Созданная статья
        """
        article_model = ArticleModel.from_entity(article)
        self.session.add(article_model)
        await self.session.commit()
        await self.session.refresh(article_model)
        return article_model.to_entity()
    
    async def get_by_number(self, number: str) -> Optional[Article]:
        """
        Получить статью по номеру
        
        Args:
            number: Номер статьи (например, "80")
            
        Returns:
            Article | None: Статья или None, если не найдена
        """
        stmt = select(ArticleModel).where(ArticleModel.number == number)
        result = await self.session.execute(stmt)
        article_model = result.scalar_one_or_none()
        
        if article_model:
            return article_model.to_entity()
        return None
    
    async def get_by_id(self, article_id: int) -> Optional[Article]:
        """
        Получить статью по ID
        
        Args:
            article_id: ID статьи в БД
            
        Returns:
            Article | None: Статья или None
        """
        stmt = select(ArticleModel).where(ArticleModel.id == article_id)
        result = await self.session.execute(stmt)
        article_model = result.scalar_one_or_none()
        
        if article_model:
            return article_model.to_entity()
        return None
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Article]:
        """
        Получить все статьи (с пагинацией)
        
        Args:
            limit: Максимальное количество статей
            offset: Смещение (для пагинации)
            
        Returns:
            List[Article]: Список статей
        """
        stmt = select(ArticleModel).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        article_models = result.scalars().all()
        
        return [model.to_entity() for model in article_models]
    
    async def search(self, query: str, limit: int = 10) -> List[Article]:
        """
        Полнотекстовый поиск по статьям
        
        Использует PostgreSQL pg_trgm для нечёткого поиска
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Article]: Список найденных статей
        """
        # Поиск по названию и контенту (PostgreSQL ILIKE для нечёткого поиска)
        search_pattern = f"%{query}%"
        stmt = (
            select(ArticleModel)
            .where(
                or_(
                    ArticleModel.title.ilike(search_pattern),
                    ArticleModel.content.ilike(search_pattern),
                    ArticleModel.number.ilike(search_pattern),
                )
            )
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        article_models = result.scalars().all()
        
        return [model.to_entity() for model in article_models]
    
    async def search_by_similarity(self, query: str, limit: int = 10) -> List[Article]:
        """
        Поиск по схожести (для PostgreSQL с pg_trgm)
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Article]: Список статей, отсортированных по релевантности
        """
        # Используем similarity из pg_trgm (требует PostgreSQL + расширение pg_trgm)
        stmt = (
            select(ArticleModel)
            .where(
                or_(
                    func.similarity(ArticleModel.content, query) > 0.1,
                    func.similarity(ArticleModel.title, query) > 0.1,
                )
            )
            .order_by(func.similarity(ArticleModel.content, query).desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        article_models = result.scalars().all()
        
        return [model.to_entity() for model in article_models]
    
    async def update(self, number: str, article: Article) -> Optional[Article]:
        """
        Обновить статью
        
        Args:
            number: Номер статьи
            article: Обновлённая статья
            
        Returns:
            Article | None: Обновлённая статья или None
        """
        stmt = (
            update(ArticleModel)
            .where(ArticleModel.number == number)
            .values(
                title=article.title,
                content=article.content,
                chapter=article.chapter,
            )
            .returning(ArticleModel)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        article_model = result.scalar_one_or_none()
        
        if article_model:
            return article_model.to_entity()
        return None
    
    async def delete(self, number: str) -> bool:
        """
        Удалить статью
        
        Args:
            number: Номер статьи
            
        Returns:
            bool: True, если статья удалена
        """
        stmt = delete(ArticleModel).where(ArticleModel.number == number)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def count(self) -> int:
        """
        Получить общее количество статей
        
        Returns:
            int: Количество статей в БД
        """
        stmt = select(func.count(ArticleModel.id))
        result = await self.session.execute(stmt)
        return result.scalar_one()


# ============================================================================
# CONVERSATION REPOSITORY
# ============================================================================

class ConversationRepository:
    """
    Репозиторий для работы с диалогами
    
    Операции:
    - Создание диалога
    - Получение диалога по ID
    - Получение диалогов пользователя
    - Добавление сообщения в диалог
    - Обновление диалога
    - Удаление диалога
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, conversation: LegalConversation) -> LegalConversation:
        """
        Создать новый диалог
        
        Args:
            conversation: Доменная сущность диалога
            
        Returns:
            LegalConversation: Созданный диалог
        """
        conversation_model = ConversationModel.from_entity(conversation)
        self.session.add(conversation_model)
        await self.session.commit()
        await self.session.refresh(conversation_model)
        return conversation_model.to_entity()
    
    async def get_by_id(self, conversation_id: int) -> Optional[LegalConversation]:
        """
        Получить диалог по ID
        
        Args:
            conversation_id: ID диалога
            
        Returns:
            LegalConversation | None: Диалог или None
        """
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .options(selectinload(ConversationModel.messages))
        )
        result = await self.session.execute(stmt)
        conversation_model = result.scalar_one_or_none()
        
        if conversation_model:
            return conversation_model.to_entity()
        return None
    
    async def get_by_user_id(
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[LegalConversation]:
        """
        Получить все диалоги пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество диалогов
            offset: Смещение
            
        Returns:
            List[LegalConversation]: Список диалогов
        """
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .options(selectinload(ConversationModel.messages))
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        conversation_models = result.scalars().all()
        
        return [model.to_entity() for model in conversation_models]
    
    async def get_latest_by_user_id(self, user_id: str) -> Optional[LegalConversation]:
        """
        Получить последний диалог пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            LegalConversation | None: Последний диалог или None
        """
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .options(selectinload(ConversationModel.messages))
            .order_by(ConversationModel.updated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        conversation_model = result.scalar_one_or_none()
        
        if conversation_model:
            return conversation_model.to_entity()
        return None
    
    async def add_message(
        self, 
        conversation_id: int, 
        message: LegalQuery | LegalAnswer
    ) -> LegalConversation:
        """
        Добавить сообщение в диалог
        
        Args:
            conversation_id: ID диалога
            message: Сообщение (запрос или ответ)
            
        Returns:
            LegalConversation: Обновлённый диалог
        """
        # Создаём модель сообщения
        if isinstance(message, LegalQuery):
            message_model = MessageModel.from_query(message, conversation_id)
        elif isinstance(message, LegalAnswer):
            message_model = MessageModel.from_answer(message, conversation_id)
        else:
            raise ValueError(f"Неподдерживаемый тип сообщения: {type(message)}")
        
        self.session.add(message_model)
        await self.session.commit()
        
        # Возвращаем обновлённый диалог
        return await self.get_by_id(conversation_id)
    
    async def update(self, conversation: LegalConversation) -> LegalConversation:
        """
        Обновить диалог
        
        Args:
            conversation: Обновлённый диалог
            
        Returns:
            LegalConversation: Обновлённый диалог
        """
        # Это упрощённая версия - полная реализация требует маппинга всех изменений
        # Для production нужно более сложное обновление с отслеживанием изменений
        
        stmt = (
            update(ConversationModel)
            .where(ConversationModel.user_id == conversation.user_id)
            .values(
                metadata_json=conversation.metadata,
            )
            .returning(ConversationModel)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        conversation_model = result.scalar_one_or_none()
        
        if conversation_model:
            return conversation_model.to_entity()
        return conversation
    
    async def delete(self, conversation_id: int) -> bool:
        """
        Удалить диалог (каскадно удалит все сообщения)
        
        Args:
            conversation_id: ID диалога
            
        Returns:
            bool: True, если диалог удалён
        """
        stmt = delete(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def delete_by_user_id(self, user_id: str) -> int:
        """
        Удалить все диалоги пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество удалённых диалогов
        """
        stmt = delete(ConversationModel).where(ConversationModel.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount
    
    async def count_by_user_id(self, user_id: str) -> int:
        """
        Получить количество диалогов пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество диалогов
        """
        stmt = select(func.count(ConversationModel.id)).where(
            ConversationModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
