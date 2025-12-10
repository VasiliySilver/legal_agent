"""API роуты для работы со статьями ТК РФ."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.api.dependencies import (
    get_db_session,
    get_search_articles_use_case,
)
from src.api.schemas import (
    SearchArticlesRequest,
    SearchArticlesResponse,
    ArticleResponse,
    SearchStrategyEnum,
)
from src.application.use_cases.search_articles import SearchArticlesUseCase, SearchStrategy
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get(
    "",
    response_model=SearchArticlesResponse,
    status_code=status.HTTP_200_OK,
    summary="Поиск статей ТК РФ",
    description="Поиск статей по номеру, тексту или семантике",
)
async def search_articles(
    query: str = Query(..., description="Поисковый запрос"),
    strategy: SearchStrategyEnum = Query(
        SearchStrategyEnum.SEMANTIC,
        description="Стратегия поиска"
    ),
    limit: int = Query(5, ge=1, le=50, description="Количество результатов"),
    session: AsyncSession = Depends(get_db_session),
    search_uc: SearchArticlesUseCase = Depends(get_search_articles_use_case),
) -> SearchArticlesResponse:
    """
    Поиск статей ТК РФ.
    
    Args:
        query: Поисковый запрос
        strategy: Стратегия поиска (by_number, fulltext, semantic)
        limit: Количество результатов
        session: Сессия БД
        search_uc: Use case для поиска статей
    
    Returns:
        SearchArticlesResponse: Найденные статьи
    """
    try:
        logger.info(f"Поиск статей: query='{query}', strategy={strategy}, limit={limit}")
        
        # Конвертируем enum в SearchStrategy
        strategy_map = {
            SearchStrategyEnum.BY_NUMBER: SearchStrategy.BY_NUMBER,
            SearchStrategyEnum.FULLTEXT: SearchStrategy.FULLTEXT,
            SearchStrategyEnum.SEMANTIC: SearchStrategy.SEMANTIC,
        }
        
        search_strategy = strategy_map[strategy]
        
        # Выполняем поиск
        articles = await search_uc.search(
            query=query,
            strategy=search_strategy,
            limit=limit,
        )
        
        logger.info(f"Найдено статей: {len(articles)}")
        
        return SearchArticlesResponse(
            articles=[
                ArticleResponse(
                    number=article.number,
                    title=article.title,
                    content=article.content,
                    chapter=article.chapter,
                )
                for article in articles
            ],
            total=len(articles),
            strategy=strategy.value,
        )
    
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Ошибка поиска статей: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при поиске статей",
        )


@router.get(
    "/{article_number}",
    response_model=ArticleResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить статью по номеру",
    description="Возвращает полный текст статьи ТК РФ по номеру",
)
async def get_article_by_number(
    article_number: str,
    session: AsyncSession = Depends(get_db_session),
    search_uc: SearchArticlesUseCase = Depends(get_search_articles_use_case),
) -> ArticleResponse:
    """
    Получить статью по номеру.
    
    Args:
        article_number: Номер статьи (например, '80')
        session: Сессия БД
        search_uc: Use case для поиска статей
    
    Returns:
        ArticleResponse: Статья ТК РФ
    
    Raises:
        HTTPException: Если статья не найдена
    """
    try:
        logger.info(f"Запрос статьи по номеру: {article_number}")
        
        # Ищем по номеру
        article = await search_uc.search_by_number(article_number)
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Статья {article_number} не найдена",
            )
        
        logger.info(f"Статья найдена: {article.number}")
        
        return ArticleResponse(
            number=article.number,
            title=article.title,
            content=article.content,
            chapter=article.chapter,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статьи: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статьи",
        )


@router.post(
    "/search",
    response_model=SearchArticlesResponse,
    status_code=status.HTTP_200_OK,
    summary="Поиск статей (POST)",
    description="Поиск статей с телом запроса",
)
async def search_articles_post(
    request: SearchArticlesRequest,
    session: AsyncSession = Depends(get_db_session),
    search_uc: SearchArticlesUseCase = Depends(get_search_articles_use_case),
) -> SearchArticlesResponse:
    """
    Поиск статей через POST запрос.
    
    Args:
        request: Параметры поиска
        session: Сессия БД
        search_uc: Use case для поиска статей
    
    Returns:
        SearchArticlesResponse: Найденные статьи
    """
    try:
        logger.info(f"POST поиск статей: query='{request.query}', strategy={request.strategy}")
        
        # Конвертируем enum в SearchStrategy
        strategy_map = {
            SearchStrategyEnum.BY_NUMBER: SearchStrategy.BY_NUMBER,
            SearchStrategyEnum.FULLTEXT: SearchStrategy.FULLTEXT,
            SearchStrategyEnum.SEMANTIC: SearchStrategy.SEMANTIC,
        }
        
        search_strategy = strategy_map[request.strategy]
        
        # Выполняем поиск
        articles = await search_uc.search(
            query=request.query,
            strategy=search_strategy,
            limit=request.limit,
        )
        
        logger.info(f"Найдено статей: {len(articles)}")
        
        return SearchArticlesResponse(
            articles=[
                ArticleResponse(
                    number=article.number,
                    title=article.title,
                    content=article.content,
                    chapter=article.chapter,
                )
                for article in articles
            ],
            total=len(articles),
            strategy=request.strategy.value,
        )
    
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Ошибка поиска статей: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при поиске статей",
        )
