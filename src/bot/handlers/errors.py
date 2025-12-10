"""
Обработчик ошибок для Telegram бота.
Ловит все необработанные исключения.
"""

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from src.bot.keyboards.builders import build_main_menu
from src.bot.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)

router = Router(name="errors")


@router.error()
async def error_handler(event: ErrorEvent) -> None:
    """
    Глобальный обработчик ошибок.
    Логирует исключения и отправляет пользователю понятное сообщение.
    """
    logger.error(
        f"Update {event.update.update_id} caused error: {event.exception}",
        exc_info=event.exception,
    )
    
    # Пытаемся отправить сообщение пользователю
    if event.update.message:
        message = event.update.message
    elif event.update.callback_query:
        message = event.update.callback_query.message
    else:
        # Если нет сообщения - просто логируем
        return
    
    try:
        error_text = (
            "❌ *Произошла ошибка*\n\n"
            "Что\\-то пошло не так при обработке твоего запроса\\.\n\n"
            "Пожалуйста, попробуй ещё раз или обратись к администратору\\."
        )
        
        keyboard = build_main_menu()
        
        await message.answer(
            text=error_text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
        
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")