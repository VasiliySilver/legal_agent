"""
Форматирование ответов для отправки в Telegram.
Использует Markdown V2 для красивого отображения.
"""

from typing import Any


def escape_markdown(text: str) -> str:
    """
    Экранирование специальных символов для Telegram Markdown V2.

    Args:
        text: Исходный текст

    Returns:
        Текст с экранированными специальными символами
    """
    # Символы, требующие экранирования в Markdown V2
    special_chars = r"_*[]()~`>#+-=|{}.!"

    for char in special_chars:
        text = text.replace(char, f"\\{char}")

    return text


def format_article(
    article: dict[str, Any],
    max_content_length: int = 500,
) -> str:
    """
    Форматирование одной статьи ТК РФ.

    Args:
        article: Словарь со статьёй (number, title, content)
        max_content_length: Максимальная длина контента

    Returns:
        Отформатированная статья для Telegram
    """
    number = article.get("number", "N/A")
    title = article.get("title", "Без названия")
    content = article.get("content", "")

    # Обрезаем длинный контент
    if len(content) > max_content_length:
        content = content[:max_content_length] + "..."

    # Экранируем для Markdown V2
    number_escaped = escape_markdown(str(number))
    title_escaped = escape_markdown(title)
    content_escaped = escape_markdown(content)

    return f"📄 *Статья {number_escaped}*\n_{title_escaped}_\n\n{content_escaped}"


def format_articles_list(
    articles: list[dict[str, Any]],
    max_articles: int = 5,
) -> str:
    """
    Форматирование списка статей.

    Args:
        articles: Список статей
        max_articles: Максимальное количество статей для отображения

    Returns:
        Отформатированный список статей
    """
    if not articles:
        return "❌ Статьи не найдены"

    # Ограничиваем количество статей
    articles_to_show = articles[:max_articles]

    header = f"📚 *Найдено статей: {len(articles)}*\n\n"

    formatted_articles = []
    for article in articles_to_show:
        formatted_articles.append(format_article(article, max_content_length=300))

    result = header + "\n\n".join(formatted_articles)

    if len(articles) > max_articles:
        more = len(articles) - max_articles
        result += f"\n\n_\\.\\.\\. и ещё {more} статей_"

    return result


def format_answer(response: dict[str, Any]) -> str:
    """
    Форматирование ответа от API для отправки пользователю.

    Args:
        response: Ответ от API (answer, articles, confidence)

    Returns:
        Отформатированный ответ для Telegram
    """
    answer = response.get("answer", "Нет ответа")
    articles = response.get("articles", [])
    confidence = response.get("confidence", 0.0)

    # Выбираем эмодзи в зависимости от уверенности
    if confidence >= 0.8:
        confidence_emoji = "✅"
        confidence_text = "высокая уверенность"
    elif confidence >= 0.6:
        confidence_emoji = "⚠️"
        confidence_text = "средняя уверенность"
    else:
        confidence_emoji = "❌"
        confidence_text = "низкая уверенность, не уверен в ответе"

    # Экранируем ответ
    answer_escaped = escape_markdown(answer)
    confidence_text_escaped = escape_markdown(confidence_text)

    # Формируем результат
    result = f"💬 *Ответ:*\n\n{answer_escaped}\n\n"
    result += f"{confidence_emoji} _{confidence_text_escaped}_"

    # Добавляем статьи, если они есть
    if articles:
        result += "\n\n" + "─" * 30 + "\n\n"
        result += format_articles_list(articles, max_articles=3)

    return result


def format_conversation_history(
    conversation: dict[str, Any],
    max_messages: int = 10,
) -> str:
    """
    Форматирование истории диалога.

    Args:
        conversation: Диалог с сообщениями
        max_messages: Максимальное количество сообщений

    Returns:
        Отформатированная история
    """
    messages = conversation.get("messages", [])

    if not messages:
        return "❌ История пуста"

    # Берём последние N сообщений
    messages_to_show = messages[-max_messages:]

    header = "📜 *История диалога*\n\n"

    formatted_messages = []
    for msg in messages_to_show:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Обрезаем длинные сообщения
        if len(content) > 200:
            content = content[:200] + "..."

        content_escaped = escape_markdown(content)

        if role == "user":
            emoji = "👤"
            role_text = "Вы"
        else:
            emoji = "🤖"
            role_text = "Ассистент"

        role_escaped = escape_markdown(role_text)
        formatted_messages.append(f"{emoji} *{role_escaped}:*\n{content_escaped}")

    result = header + "\n\n".join(formatted_messages)

    if len(messages) > max_messages:
        result = (
            f"_Показаны последние {max_messages} сообщений из {len(messages)}_\n\n"
            + result
        )

    return result
