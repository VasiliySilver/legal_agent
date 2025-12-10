"""
LLM сервис для генерации ответов на юридические вопросы.

Использует Groq API для обработки запросов с контекстом статей ТК РФ.
"""

import re
from typing import Optional

from groq import AsyncGroq

from src.domain.entities import Article, LegalAnswer, Message


class LLMService:
    """Сервис для работы с LLM (Large Language Model)."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        proxy: Optional[str] = None,
    ):
        """
        Инициализация LLM сервиса.

        Args:
            api_key: API ключ для Groq
            model: Название модели (по умолчанию llama-3.3-70b-versatile)
            proxy: Прокси URL (опционально)
        """
        # Создаем клиент с поддержкой прокси если указан
        client_kwargs = {"api_key": api_key}
        if proxy:
            import httpx

            client_kwargs["http_client"] = httpx.AsyncClient(proxy=proxy)

        self.client = AsyncGroq(**client_kwargs)
        self.model = model
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """
        Получить системный промпт для LLM.

        Returns:
            Системный промпт с инструкциями для модели
        """
        return """Ты — юридический помощник, специализирующийся на Трудовом кодексе РФ.

Твоя задача:
1. Отвечать на вопросы пользователей о трудовом праве
2. Использовать только предоставленные статьи ТК РФ в качестве источников
3. Давать точные, понятные и структурированные ответы
4. Указывать номера статей, на которые ты ссылаешься
5. Если вопрос не относится к трудовому праву, вежливо сообщить об этом

Формат ответа:
- Краткий и понятный ответ на вопрос
- Ссылки на конкретные статьи ТК РФ
- При необходимости - цитаты из статей

Важно:
- Не выдумывай информацию, используй только предоставленный контекст
- Если недостаточно информации, честно об этом скажи
- Пиши простым языком, избегай сложных юридических терминов где возможно
"""

    def _format_articles_context(self, articles: list[Article]) -> str:
        """
        Форматирование статей для контекста промпта.

        Args:
            articles: Список статей ТК РФ

        Returns:
            Отформатированный текст со статьями
        """
        if not articles:
            return "Релевантные статьи ТК РФ не найдены."

        context_parts = ["Релевантные статьи ТК РФ:\n"]

        for article in articles:
            context_parts.append(f"\n{'=' * 60}")
            context_parts.append(f"Статья {article.number}. {article.title}")
            context_parts.append(f"Глава: {article.chapter}")
            context_parts.append(f"\n{article.content}")
            context_parts.append(f"{'=' * 60}\n")

        return "\n".join(context_parts)

    def _format_history(self, history: list[Message]) -> list[dict[str, str]]:
        """
        Форматирование истории диалога для LLM.

        Args:
            history: История сообщений

        Returns:
            Список словарей с ролями и контентом
        """
        formatted = []
        for message in history:
            formatted.append({"role": message.role, "content": message.content})
        return formatted

    async def generate_answer(
        self,
        question: str,
        articles: list[Article],
        history: Optional[list[Message]] = None,
    ) -> LegalAnswer:
        """
        Генерация ответа на юридический вопрос.

        Args:
            question: Вопрос пользователя
            articles: Релевантные статьи ТК РФ
            history: История диалога (опционально)

        Returns:
            Ответ с источниками и уверенностью

        Raises:
            Exception: При ошибке обращения к API
        """
        # Формируем контекст из статей
        articles_context = self._format_articles_context(articles)

        # Формируем сообщения для LLM
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
        ]

        # Добавляем историю диалога, если есть
        if history:
            messages.extend(self._format_history(history))

        # Добавляем контекст статей и вопрос
        user_message = f"{articles_context}\n\nВопрос: {question}"
        messages.append({"role": "user", "content": user_message})

        try:
            # Вызываем API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Низкая температура для более точных ответов
                max_tokens=1000,
            )

            # Извлекаем ответ
            answer_text = response.choices[0].message.content

            # Извлекаем номера статей из ответа
            sources = self._extract_article_numbers(answer_text)

            # Если не нашли источники в ответе, используем исходные статьи
            if not sources and articles:
                sources = [int(a.number) for a in articles if a.number.isdigit()]

            # Определяем уверенность на основе наличия статей
            confidence = self._calculate_confidence(articles, sources)

            # Конвертируем номера статей в строки
            article_numbers = [str(s) for s in sources]

            return LegalAnswer(
                answer=answer_text,
                context=articles,  # Полные объекты статей
                sources=sources,  # Номера статей как int (для обратной совместимости)
                article_numbers=article_numbers,  # Номера статей как строки
                confidence=confidence,
            )

        except Exception as e:
            # Логируем ошибку и возвращаем fallback ответ
            print(f"Error calling LLM API: {e}")
            return LegalAnswer(
                answer="Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже.",
                context=[],
                sources=[],
                article_numbers=[],
                confidence=0.0,
            )

    def _extract_article_numbers(self, text: str) -> list[int]:
        """
        Извлечение номеров статей из текста ответа.

        Args:
            text: Текст ответа LLM

        Returns:
            Список номеров статей
        """
        # Ищем паттерны типа "статья 80", "статье 77", "статьи 80"
        # Также ловим "статьям 80 и 77" (где 77 идёт после "и")
        pattern = r"стать[иеюя][мх]?\s+(\d+(?:\s+и\s+\d+)*)"
        matches = re.findall(pattern, text, re.IGNORECASE)

        # Извлекаем все числа из найденных совпадений
        numbers = []
        for match in matches:
            # Извлекаем все числа из каждого совпадения
            nums = re.findall(r"\d+", match)
            numbers.extend(int(num) for num in nums)

        # Удаляем дубликаты и сортируем
        return sorted(list(set(numbers)))

    def _calculate_confidence(
        self, articles: list[Article], sources: list[int]
    ) -> float:
        """
        Расчёт уверенности в ответе.

        Args:
            articles: Найденные статьи
            sources: Использованные источники

        Returns:
            Уровень уверенности от 0.0 до 1.0
        """
        if not articles:
            return 0.1  # Очень низкая уверенность без статей

        if not sources:
            return 0.5  # Средняя уверенность если статьи есть, но не извлечены

        # Высокая уверенность если есть и статьи и источники
        return 0.95


def extract_article_numbers(text: str) -> list[int]:
    """
    Утилита для извлечения номеров статей из текста.

    Args:
        text: Текст для анализа

    Returns:
        Список номеров статей
    """
    pattern = r"стать[иеюя][мх]?\s+(\d+(?:\s+и\s+\d+)*)"
    matches = re.findall(pattern, text, re.IGNORECASE)

    # Извлекаем все числа из найденных совпадений
    numbers = []
    for match in matches:
        # Извлекаем все числа из каждого совпадения
        nums = re.findall(r"\d+", match)
        numbers.extend(int(num) for num in nums)

    # Удаляем дубликаты и сортируем
    return sorted(list(set(numbers)))
