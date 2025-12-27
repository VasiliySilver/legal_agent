"""
FSM состояния для задавания вопросов и работы с диалогами.
"""

from aiogram.fsm.state import State, StatesGroup


class QuestionStates(StatesGroup):
    """
    Состояния для процесса задавания вопроса.
    """

    # Ожидание вопроса от пользователя
    waiting_for_question = State()

    # Обработка вопроса (показываем "typing...")
    processing_question = State()

    # Ожидание уточнения (если нужно)
    waiting_for_clarification = State()


class SearchStates(StatesGroup):
    """
    Состояния для поиска статей.
    """

    # Ожидание поискового запроса
    waiting_for_query = State()

    # Просмотр результатов поиска
    viewing_results = State()

    # Просмотр конкретной статьи
    viewing_article = State()


class ConversationStates(StatesGroup):
    """
    Состояния для работы с диалогами.
    """

    # Просмотр списка диалогов
    viewing_list = State()

    # Просмотр конкретного диалога
    viewing_conversation = State()

    # Активный диалог (продолжение беседы)
    active_conversation = State()
