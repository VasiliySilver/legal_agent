"""Use cases (варианты использования) приложения."""

from src.application.use_cases.MultiStrategySearchUseCase import MultiStrategySearchUseCase
from src.application.use_cases.conversation_orchestrator import ConversationOrchestrator
from src.application.use_cases.quick_answer_use_case import QuickAnswerUseCase
from src.application.use_cases.answer_legal_question import (
    AnswerLegalQuestionUseCase,
)
from src.application.use_cases.manage_conversation import (
    ManageConversationUseCase,
)
from src.application.use_cases.search_articles import (
    SearchArticlesUseCase,
    ArticleExplorerUseCase,
    SearchStrategy,
)

__all__ = [
    # Ответ на вопросы
    "AnswerLegalQuestionUseCase",
    "QuickAnswerUseCase",
    # Управление диалогами
    "ManageConversationUseCase",
    "ConversationOrchestrator",
    # Поиск статей
    "SearchArticlesUseCase",
    "MultiStrategySearchUseCase",
    "ArticleExplorerUseCase",
    "SearchStrategy",
]
