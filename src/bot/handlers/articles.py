"""
Обработчики для поиска и просмотра статей РФ.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.api_client import LegalAgentAPIClient
from src.bot.keyboards.builders import (
    build_article_keyboard,
    build_articles_list_keyboard,
    build_main_menu,
)
from src.bot.keyboards.callbacks import (
    ArticleCallback,
    CallbackAction,
    MenuCallback,
)
from src.bot.states.question import SearchStates
from src.bot.utils.formatters import escape_markdown, format_article, format_articles_list

logger = logging.getLogger(__name__)

router = Router(name="articles")


@router.callback_query(MenuCallback.filter(F.action == CallbackAction.SEARCH))
async def start_search(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Начало поиска статей.
    Устанавливаем состояние и ждём поисковый запрос.
    """
    await callback.answer()
    
    # Устанавливаем состояние ожидания запроса
    await state.set_state(SearchStates.waiting_for_query)
    
    text = (
        "🔍 *Поиск статей ТК РФ*\n\n"
        "Введи номер статьи или ключевые слова для поиска\\.\n\n"
        "_Примеры:_\n"
        "• 21 \\(для поиска статьи 21\\)\n"
        "• права работника\n"
        "• отпуск\n"
        "• увольнение\n\n"
        "Отправь /cancel для отмены\\."
    )
    
    await callback.message.edit_text(
        text=text,
        parse_mode="MarkdownV2",
    )
    
    logger.info(f"User {callback.from_user.id} started article search")


@router.message(SearchStates.waiting_for_query, F.text)
async def process_search(
    message: Message,
    state: FSMContext,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Обработка поискового запроса.
    """
    query = message.text
    
    # Показываем индикатор "печатает..."
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action="typing",
    )
    
    try:
        # Выполняем поиск через API
        response = await api_client.search_articles(query=query, limit=10)
        articles = response.get("articles", [])
        
        if not articles:
            text = (
                f"❌ По запросу \"{escape_markdown(query)}\" ничего не найдено\\.\n\n"
                "Попробуй изменить запрос или используй другие ключевые слова\\."
            )
            keyboard = build_main_menu()
            
            await message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )
        else:
            # Форматируем список статей
            formatted_list = format_articles_list(articles, max_articles=5)
            keyboard = build_articles_list_keyboard(articles[:5])
            
            await message.answer(
                text=formatted_list,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )
            
            # Сохраняем результаты в состояние для пагинации
            await state.update_data(
                search_results=articles,
                current_page=1,
            )
        
        logger.info(
            f"User {message.from_user.id} searched for: {query}, found {len(articles)} articles"
        )
        
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        
        error_text = (
            "❌ *Ошибка при поиске*\n\n"
            f"Произошла ошибка: {escape_markdown(str(e))}\n\n"
            "Попробуй позже\\."
        )
        keyboard = build_main_menu()
        
        await message.answer(
            text=error_text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
    
    finally:
        # Очищаем состояние поиска
        await state.set_state(SearchStates.viewing_results)


@router.callback_query(ArticleCallback.filter(F.action == CallbackAction.VIEW))
async def view_article(
    callback: CallbackQuery,
    callback_data: ArticleCallback,
    state: FSMContext,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Просмотр конкретной статьи.
    """
    await callback.answer()
    
    article_number = callback_data.article_number
    
    try:
        # Получаем статью через API
        response = await api_client.search_articles(query=article_number, limit=1)
        articles = response.get("articles", [])
        
        if not articles:
            await callback.answer(
                text="Статья не найдена",
                show_alert=True,
            )
            return
        
        article = articles[0]
        
        # Форматируем статью
        formatted_article = format_article(article, max_content_length=1000)
        keyboard = build_article_keyboard(article_number)
        
        await callback.message.edit_text(
            text=formatted_article,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
        
        logger.info(f"User {callback.from_user.id} viewed article {article_number}")
        
    except Exception as e:
        logger.error(f"Error viewing article: {e}")
        
        await callback.answer(
            text="Ошибка при загрузке статьи",
            show_alert=True,
        )


@router.callback_query(MenuCallback.filter(F.action == CallbackAction.BACK))
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Возврат в главное меню.
    """
    await callback.answer()
    
    # Очищаем состояние
    await state.clear()
    
    text = (
        "🏠 *Главное меню*\n\n"
        "Выбери действие:"
    )
    keyboard = build_main_menu()
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )
    
    logger.info(f"User {callback.from_user.id} returned to main menu")


@router.message(SearchStates.waiting_for_query)
async def invalid_search_format(message: Message) -> None:
    """
    Обработка неправильного формата поискового запроса.
    """
    text = (
        "⚠️ Пожалуйста, отправь запрос *текстом*\\.\n\n"
        "Отправь /cancel для отмены\\."
    )
    
    await message.answer(
        text=text,
        parse_mode="MarkdownV2",
    )