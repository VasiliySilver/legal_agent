"""
Схемы callback data для inline клавиатур.
Используется aiogram.filters.callback_data для типизации.
"""

from enum import Enum

from aiogram.filters.callback_data import CallbackData


class CallbackAction(str, Enum):
    """Действия для callback кнопок."""

    HELP = "help"
    SEARCH = "search"
    VIEW = "view"
    DELETE = "delete"
    NEW = "new"
    BACK = "back"
    NEXT = "next"
    PREV = "prev"


class MenuCallback(CallbackData, prefix="menu"):
    """
    Callback для главного меню.
    Формат: menu:action
    """

    action: CallbackAction


class ArticleCallback(CallbackData, prefix="article"):
    """
    Callback для работы со статьями.
    Формат: article:action:number или article:action:number:page
    """

    action: CallbackAction
    article_number: str = ""  # Пустая строка вместо None
    page: int = 0  # 0 вместо None


class ConversationCallback(CallbackData, prefix="conv"):
    """
    Callback для работы с диалогами.
    Формат: conv:action или conv:action:conversation_id
    """

    action: CallbackAction
    conversation_id: str = ""  # Пустая строка вместо None
