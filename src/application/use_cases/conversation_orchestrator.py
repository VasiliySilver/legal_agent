from src.application.use_cases.manage_conversation import ManageConversationUseCase
from src.domain.entities import LegalAnswer, LegalConversation, LegalQuery


class ConversationOrchestratorUseCase:
    """
    Оркестратор для управления полным циклом диалога.

    Комбинирует ManageConversationUseCase и AnswerLegalQuestionUseCase
    для создания законченного диалогового опыта.
    """

    def __init__(
        self,
        answer_use_case,  # AnswerLegalQuestionUseCase (избегаем циклического импорта)
        manage_conversation_use_case: ManageConversationUseCase,
    ):
        """
        Инициализация оркестратора.

        Args:
            answer_use_case: Use case ответа на вопросы
            manage_conversation_use_case: Use case управления диалогами
        """
        self.answer_use_case = answer_use_case
        self.manage_conversation_use_case = manage_conversation_use_case

    async def start_new_dialog(
        self,
        user_id: str,
        first_question: str,
    ) -> tuple[LegalConversation, LegalAnswer]:
        """
        Начать новый диалог с первым вопросом.

        Args:
            user_id: ID пользователя
            first_question: Первый вопрос пользователя

        Returns:
            Кортеж (диалог, ответ)
        """
        # Создаём новый диалог
        conversation = await self.manage_conversation_use_case.create_conversation(user_id)

        # Создаём запрос
        query = LegalQuery(
            question=first_question,
            user_id=user_id,
        )

        # Добавляем вопрос в диалог
        await self.manage_conversation_use_case.add_user_message(
            conversation.id, query
        )

        # Получаем ответ
        answer = await self.answer_use_case.execute(
            query=query,
            conversation_id=conversation.id,
        )

        # Устанавливаем conversation_id в ответе
        answer.conversation_id = conversation.id

        # Добавляем ответ в диалог
        await self.manage_conversation_use_case.add_assistant_message(
            conversation.id, answer
        )

        # Возвращаем обновлённый диалог
        updated_conversation = await self.manage_conversation_use_case.get_conversation(
            conversation.id
        )

        return updated_conversation, answer

    async def continue_dialog(
        self,
        conversation_id: int,
        question: str,
        user_id: str,
    ) -> tuple[LegalConversation, LegalAnswer]:
        """
        Продолжить существующий диалог.

        Args:
            conversation_id: ID диалога
            question: Новый вопрос
            user_id: ID пользователя

        Returns:
            Кортеж (обновлённый диалог, ответ)
        """
        # Проверяем существование диалога
        conversation = await self.manage_conversation_use_case.get_conversation(
            conversation_id
        )

        # Создаём запрос
        query = LegalQuery(
            question=question,
            user_id=user_id,
        )

        # Добавляем вопрос
        await self.manage_conversation_use_case.add_user_message(
            conversation_id, query
        )

        # Получаем ответ с учётом контекста диалога
        answer = await self.answer_use_case.execute(
            query=query,
            conversation_id=conversation_id,
        )

        # Устанавливаем conversation_id в ответе
        answer.conversation_id = conversation_id

        # Добавляем ответ
        await self.manage_conversation_use_case.add_assistant_message(
            conversation_id, answer
        )

        # Возвращаем обновлённый диалог
        updated_conversation = await self.manage_conversation_use_case.get_conversation(
            conversation_id
        )

        return updated_conversation, answer

    async def get_or_create_conversation(
        self, user_id: str
    ) -> LegalConversation:
        """
        Получить последний диалог пользователя или создать новый.

        Args:
            user_id: ID пользователя

        Returns:
            Диалог (существующий или новый)
        """
        # Пытаемся получить последний диалог
        conversation = await self.manage_conversation_use_case.get_latest_conversation(
            user_id
        )

        # Если нет, создаём новый
        if not conversation:
            conversation = await self.manage_conversation_use_case.create_conversation(
                user_id
            )

        return conversation

    async def handle_question(self, query: LegalQuery) -> LegalAnswer:
        """
        Обработать вопрос с автоматическим управлением диалогом.

        Если conversation_id указан, продолжает существующий диалог.
        Иначе создаёт новый диалог или использует последний активный.

        Args:
            query: Запрос пользователя

        Returns:
            Ответ на вопрос
        """
        if query.conversation_id:
            # Продолжаем существующий диалог
            _, answer = await self.continue_dialog(
                conversation_id=query.conversation_id,
                question=query.question,
                user_id=query.user_id,
            )
        else:
            # Начинаем новый диалог
            _, answer = await self.start_new_dialog(
                user_id=query.user_id,
                first_question=query.question,
            )

        return answer