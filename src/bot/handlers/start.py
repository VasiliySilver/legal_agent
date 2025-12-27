"""
Обработчики команд /start и /help.
Приветствие и справочная информация.
"""

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.bot.keyboards.builders import build_main_menu
from src.bot.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Обработчик команды /start.
    Приветствие и главное меню.
    """
    user = message.from_user
    username = user.username or user.first_name or "Пользователь"

    welcome_text = (
        f"👋 Привет, *{escape_markdown(username)}*\\!\n\n"
        f"Я — *Legal Agent*, твой юридический помощник по Трудовому Кодексу РФ\\.\n\n"
        f"🔹 *Что я умею:*\n"
        f"• Отвечать на вопросы по ТК РФ\n"
        f"• Искать нужные статьи\n"
        f"• Вести историю диалогов\n"
        f"• Помогать разобраться в трудовых правах\n\n"
        f"Выбери действие из меню ниже 👇"
    )

    keyboard = build_main_menu()

    await message.answer(
        text=welcome_text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )

    logger.info(f"User {user.id} started the bot")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Обработчик команды /help.
    Справочная информация о боте.
    """
    help_text = (
        "ℹ️ *Справка по использованию бота*\n\n"
        "*Доступные команды:*\n"
        "/start \\- Главное меню\n"
        "/help \\- Эта справка\n\n"
        "*Как задать вопрос:*\n"
        '1\\. Нажми кнопку "❓ Задать вопрос"\n'
        "2\\. Отправь свой вопрос текстом\n"
        "3\\. Получи развёрнутый ответ со ссылками на статьи ТК РФ\n\n"
        "*Поиск статей:*\n"
        '• Нажми "🔍 Поиск статей"\n'
        "• Введи номер статьи или ключевые слова\n"
        "• Просмотри результаты\n\n"
        "*История диалогов:*\n"
        "• Все твои вопросы сохраняются\n"
        "• Можно продолжить предыдущий диалог\n"
        '• Доступ через "📜 История диалогов"\n\n'
        "*Важно:*\n"
        "Бот предоставляет информацию по ТК РФ, но не заменяет консультацию юриста\\."
    )

    keyboard = build_main_menu()

    await message.answer(
        text=help_text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )

    logger.info(f"User {message.from_user.id} requested help")
