"""
Обработчики для работы с историей диалогов.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.bot.api_client import LegalAgentAPIClient
from src.bot.keyboards.builders import (
    build_conversation_keyboard,
    build_conversations_list_keyboard,
    build_main_menu,
)
from src.bot.keyboards.callbacks import CallbackAction, ConversationCallback
from src.bot.utils.formatters import escape_markdown, format_conversation_history

logger = logging.getLogger(__name__)

router = Router(name="conversations")


@router.callback_query(ConversationCallback.filter(F.action == CallbackAction.VIEW))
async def view_conversations_list(
    callback: CallbackQuery,
    callback_data: ConversationCallback,
    state: FSMContext,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Просмотр списка диалогов пользователя.
    Если передан conversation_id - показываем конкретный диалог.
    """
    await callback.answer()
    
    conversation_id = callback_data.conversation_id
    
    # Если есть ID - показываем конкретный диалог
    if conversation_id:
        await view_conversation_detail(callback, conversation_id, api_client)
        return
    
    # Иначе показываем список всех диалогов
    user_id = str(callback.from_user.id)
    
    try:
        # TODO: API должен вернуть список диалогов пользователя
        # Пока делаем заглушку
        conversations = []
        
        if not conversations:
            text = (
                "📜 *История диалогов*\n\n"
                "У тебя пока нет сохранённых диалогов\\.\n\n"
                "Задай первый вопрос, и он автоматически сохранится\\!"
            )
            keyboard = build_main_menu()
        else:
            text = (
                "📜 *История диалогов*\n\n"
                f"Всего диалогов: {len(conversations)}\n\n"
                "Выбери диалог для просмотра:"
            )
            keyboard = build_conversations_list_keyboard(conversations)
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
        
        logger.info(f"User {callback.from_user.id} viewed conversations list")
        
    except Exception as e:
        logger.error(f"Error viewing conversations: {e}")
        
        await callback.answer(
            text="Ошибка при загрузке диалогов",
            show_alert=True,
        )


async def view_conversation_detail(
    callback: CallbackQuery,
    conversation_id: str,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Просмотр деталей конкретного диалога.
    """
    try:
        # Получаем историю диалога через API
        conversation = await api_client.get_conversation_history(conversation_id)
        
        # Форматируем историю
        formatted_history = format_conversation_history(conversation, max_messages=10)
        keyboard = build_conversation_keyboard(conversation_id)
        
        await callback.message.edit_text(
            text=formatted_history,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
        
        logger.info(
            f"User {callback.from_user.id} viewed conversation {conversation_id}"
        )
        
    except Exception as e:
        logger.error(f"Error viewing conversation detail: {e}")
        
        await callback.answer(
            text="Ошибка при загрузке диалога",
            show_alert=True,
        )


@router.callback_query(ConversationCallback.filter(F.action == CallbackAction.NEW))
async def create_new_conversation(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Создание нового диалога.
    """
    await callback.answer()
    
    user_id = str(callback.from_user.id)
    
    try:
        # Создаём новый диалог через API
        conversation = await api_client.create_conversation(user_id)
        conversation_id = conversation.get("id")
        
        # Сохраняем ID в состояние
        await state.update_data(conversation_id=conversation_id)
        
        text = (
            "✅ *Новый диалог создан*\n\n"
            "Теперь можешь задавать вопросы\\.\n"
            "Все вопросы и ответы будут сохранены в этом диалоге\\."
        )
        keyboard = build_main_menu()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
        
        logger.info(
            f"User {callback.from_user.id} created new conversation {conversation_id}"
        )
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        
        await callback.answer(
            text="Ошибка при создании диалога",
            show_alert=True,
        )


@router.callback_query(ConversationCallback.filter(F.action == CallbackAction.DELETE))
async def delete_conversation(
    callback: CallbackQuery,
    callback_data: ConversationCallback,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Удаление диалога.
    """
    conversation_id = callback_data.conversation_id
    
    # TODO: Добавить подтверждение удаления
    
    try:
        # TODO: API endpoint для удаления диалога
        # await api_client.delete_conversation(conversation_id)
        
        await callback.answer(
            text="✅ Диалог удалён",
            show_alert=False,
        )
        
        # Возвращаемся к списку диалогов
        text = (
            "📜 *История диалогов*\n\n"
            "Диалог успешно удалён\\."
        )
        keyboard = build_main_menu()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
        
        logger.info(
            f"User {callback.from_user.id} deleted conversation {conversation_id}"
        )
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        
        await callback.answer(
            text="Ошибка при удалении диалога",
            show_alert=True,
        )