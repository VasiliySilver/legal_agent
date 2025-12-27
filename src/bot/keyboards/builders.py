"""
Билдеры для inline клавиатур Telegram.
Создают красивые и удобные кнопки для взаимодействия.
"""

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.keyboards.callbacks import (
    ArticleCallback,
    CallbackAction,
    ConversationCallback,
    MenuCallback,
)


def build_main_menu() -> InlineKeyboardMarkup:
    """
    Построение главного меню бота.

    Returns:
        Клавиатура с основными действиями
    """
    builder = InlineKeyboardBuilder()

    # Основные действия
    builder.button(
        text="❓ Задать вопрос",
        callback_data=MenuCallback(action=CallbackAction.NEW),
    )
    builder.button(
        text="🔍 Поиск статей",
        callback_data=MenuCallback(action=CallbackAction.SEARCH),
    )

    # Вторая строка
    builder.button(
        text="📜 История диалогов",
        callback_data=ConversationCallback(action=CallbackAction.VIEW),
    )
    builder.button(
        text="ℹ️ Помощь",
        callback_data=MenuCallback(action=CallbackAction.HELP),
    )

    # Устанавливаем по 2 кнопки в ряд
    builder.adjust(2, 2)

    return builder.as_markup()


def build_article_keyboard(article_number: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для просмотра статьи.

    Args:
        article_number: Номер статьи

    Returns:
        Клавиатура с действиями для статьи
    """
    builder = InlineKeyboardBuilder()

    # Кнопка "Назад к поиску"
    builder.button(
        text="🔙 Назад к поиску",
        callback_data=MenuCallback(action=CallbackAction.SEARCH),
    )

    # Кнопка "Главное меню"
    builder.button(
        text="🏠 Главное меню",
        callback_data=MenuCallback(action=CallbackAction.BACK),
    )

    builder.adjust(1)

    return builder.as_markup()


def build_articles_list_keyboard(
    articles: list[dict[str, Any]],
    current_page: int = 1,
    total_pages: int = 1,
) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком найденных статей.

    Args:
        articles: Список статей
        current_page: Текущая страница
        total_pages: Всего страниц

    Returns:
        Клавиатура со статьями и навигацией
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки статей
    for article in articles:
        number = article.get("number", "N/A")
        title = article.get("title", "Без названия")

        # Обрезаем длинные названия
        if len(title) > 40:
            title = title[:37] + "..."

        builder.button(
            text=f"📄 Статья {number}: {title}",
            callback_data=ArticleCallback(
                action=CallbackAction.VIEW,
                article_number=str(number),
            ),
        )

    # Устанавливаем по 1 кнопке в ряд для статей
    builder.adjust(1)

    # Добавляем пагинацию если нужно
    if total_pages > 1:
        pagination = build_pagination_keyboard(
            current_page=current_page,
            total_pages=total_pages,
            callback_prefix="article",
        )
        if pagination.inline_keyboard:
            builder.attach(InlineKeyboardBuilder.from_markup(pagination))

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=MenuCallback(action=CallbackAction.BACK).pack(),
        )
    )

    return builder.as_markup()


def build_conversation_keyboard(conversation_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для управления диалогом.

    Args:
        conversation_id: ID диалога

    Returns:
        Клавиатура с действиями для диалога
    """
    builder = InlineKeyboardBuilder()

    # Кнопки действий
    builder.button(
        text="💬 Продолжить диалог",
        callback_data=ConversationCallback(
            action=CallbackAction.VIEW,
            conversation_id=conversation_id,
        ),
    )

    builder.button(
        text="🗑 Удалить диалог",
        callback_data=ConversationCallback(
            action=CallbackAction.DELETE,
            conversation_id=conversation_id,
        ),
    )

    # Кнопка "Назад"
    builder.button(
        text="🔙 Назад",
        callback_data=MenuCallback(action=CallbackAction.BACK),
    )

    builder.adjust(1)

    return builder.as_markup()


def build_conversations_list_keyboard(
    conversations: list[dict[str, Any]],
) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком диалогов.

    Args:
        conversations: Список диалогов

    Returns:
        Клавиатура с диалогами
    """
    builder = InlineKeyboardBuilder()

    # Добавляем диалоги
    for idx, conv in enumerate(conversations, 1):
        conv_id = conv.get("id", "")
        created_at = conv.get("created_at", "")

        # Форматируем дату
        date_str = created_at[:10] if created_at else "N/A"

        builder.button(
            text=f"💬 Диалог {idx} ({date_str})",
            callback_data=ConversationCallback(
                action=CallbackAction.VIEW,
                conversation_id=conv_id,
            ),
        )

    builder.adjust(1)

    # Кнопка "Новый диалог"
    builder.row(
        InlineKeyboardButton(
            text="➕ Новый диалог",
            callback_data=ConversationCallback(action=CallbackAction.NEW).pack(),
        )
    )

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=MenuCallback(action=CallbackAction.BACK).pack(),
        )
    )

    return builder.as_markup()


def build_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
) -> InlineKeyboardMarkup:
    """
    Построение кнопок навигации (пагинация).

    Args:
        current_page: Текущая страница
        total_pages: Всего страниц
        callback_prefix: Префикс для callback (article/conv)

    Returns:
        Клавиатура с навигацией
    """
    builder = InlineKeyboardBuilder()

    # Если только одна страница - не нужна навигация
    if total_pages <= 1:
        return builder.as_markup()

    # Кнопка "Назад" (если не первая страница)
    if current_page > 1:
        builder.button(
            text="◀️ Назад",
            callback_data=ArticleCallback(
                action=CallbackAction.PREV,
                page=current_page - 1,
            ),
        )

    # Индикатор страницы
    builder.button(
        text=f"📄 {current_page}/{total_pages}",
        callback_data="noop",  # Неактивная кнопка
    )

    # Кнопка "Вперёд" (если не последняя страница)
    if current_page < total_pages:
        builder.button(
            text="▶️ Вперёд",
            callback_data=ArticleCallback(
                action=CallbackAction.NEXT,
                page=current_page + 1,
            ),
        )

    builder.adjust(3)

    return builder.as_markup()
