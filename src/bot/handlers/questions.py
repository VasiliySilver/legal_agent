"""
Обработчики для задавания вопросов и получения ответов.
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.api_client import LegalAgentAPIClient
from src.bot.keyboards.builders import build_main_menu
from src.bot.keyboards.callbacks import CallbackAction, MenuCallback
from src.bot.states.question import QuestionStates
from src.bot.utils.formatters import escape_markdown, format_answer

logger = logging.getLogger(__name__)

router = Router(name="questions")


@router.callback_query(MenuCallback.filter(F.action == CallbackAction.NEW))
async def start_question(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Начало процесса задавания вопроса.
    Устанавливаем FSM состояние и ждём вопрос.
    """
    await callback.answer()
    
    # Устанавливаем состояние ожидания вопроса
    await state.set_state(QuestionStates.waiting_for_question)
    
    text = (
        "❓ *Задай свой вопрос*\n\n"
        "Напиши вопрос по Трудовому Кодексу РФ, "
        "и я постараюсь дать развёрнутый ответ со ссылками на статьи\\.\n\n"
        "_Например:_\n"
        "• Какие права у работника при увольнении?\n"
        "• Сколько дней отпуска положено?\n"
        "• Что делать при задержке зарплаты?\n\n"
        "Отправь /cancel для отмены\\."
    )
    
    await callback.message.edit_text(
        text=text,
        parse_mode="MarkdownV2",
    )
    
    logger.info(f"User {callback.from_user.id} started asking a question")


@router.message(QuestionStates.waiting_for_question, F.text)
async def process_question(
    message: Message,
    state: FSMContext,
    api_client: LegalAgentAPIClient,
) -> None:
    """
    Обработка вопроса пользователя.
    Отправляем в API и возвращаем ответ.
    """
    question = message.text
    
    # Показываем индикатор "печатает..."
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action="typing",
    )
    
    try:
        # Получаем данные из состояния (conversation_id если есть)
        data = await state.get_data()
        conversation_id = data.get("conversation_id")
        
        # Отправляем вопрос в API
        response = await api_client.ask_question(
            question=question,
            conversation_id=conversation_id,
        )
        
        # Сохраняем conversation_id для следующих вопросов
        if "conversation_id" in response:
            await state.update_data(conversation_id=response["conversation_id"])
        
        # Форматируем и отправляем ответ
        formatted_answer = format_answer(response)
        keyboard = build_main_menu()
        
        await message.answer(
            text=formatted_answer,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
        
        logger.info(
            f"User {message.from_user.id} received answer for question: {question[:50]}..."
        )
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        
        error_text = (
            "❌ *Ошибка при обработке вопроса*\n\n"
            f"Произошла ошибка: {escape_markdown(str(e))}\n\n"
            "Попробуй задать вопрос позже или обратись к администратору\\."
        )
        
        keyboard = build_main_menu()
        
        await message.answer(
            text=error_text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
    
    finally:
        # Очищаем состояние
        await state.clear()


@router.message(QuestionStates.waiting_for_question)
async def invalid_question_format(message: Message) -> None:
    """
    Обработка неправильного формата вопроса.
    """
    text = (
        "⚠️ Пожалуйста, отправь вопрос *текстом*\\.\n\n"
        "Я не умею обрабатывать фото, видео или другие типы сообщений\\.\n\n"
        "Отправь /cancel для отмены\\."
    )
    
    await message.answer(
        text=text,
        parse_mode="MarkdownV2",
    )


@router.message(F.text == "/cancel")
async def cancel_question(message: Message, state: FSMContext) -> None:
    """
    Отмена текущего действия.
    """
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нечего отменять\\.", parse_mode="MarkdownV2")
        return
    
    await state.clear()
    
    text = "✅ Действие отменено\\."
    keyboard = build_main_menu()
    
    await message.answer(
        text=text,
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )
    
    logger.info(f"User {message.from_user.id} cancelled action")