"""
Тесты для форматирования ответов для Telegram.
"""

import pytest

from src.bot.utils.formatters import (
    format_answer,
    format_article,
    format_articles_list,
    format_conversation_history,
    escape_markdown,
)


def test_escape_markdown():
    """Тест: экранирование специальных символов Markdown."""
    text = "Test_with*special[chars](and)dots."
    escaped = escape_markdown(text)
    
    assert "_" not in escaped or "\\_" in escaped
    assert "*" not in escaped or "\\*" in escaped
    assert "[" not in escaped or "\\[" in escaped
    assert "]" not in escaped or "\\]" in escaped
    assert "(" not in escaped or "\\(" in escaped
    assert ")" not in escaped or "\\)" in escaped
    assert "." not in escaped or "\\." in escaped


def test_format_article():
    """Тест: форматирование одной статьи."""
    article = {
        "number": "21",
        "title": "Основные права работника",
        "content": "Работник имеет право на заключение...",
    }
    
    formatted = format_article(article)
    
    assert "Статья 21" in formatted
    assert "Основные права работника" in formatted
    assert "Работник имеет право" in formatted
    assert formatted.startswith("📄")


def test_format_article_long_content():
    """Тест: обрезка длинного контента статьи."""
    article = {
        "number": "21",
        "title": "Основные права работника",
        "content": "A" * 1000,  # Очень длинный текст
    }
    
    formatted = format_article(article, max_content_length=200)
    
    assert len(formatted) < 500  # С учётом заголовков
    # Проверяем что текст обрезан (ищем экранированное многоточие)
    assert "\\.\\.\\." in formatted or "..." in formatted


def test_format_articles_list():
    """Тест: форматирование списка статей."""
    articles = [
        {
            "number": "21",
            "title": "Основные права работника",
            "content": "Текст статьи 21",
        },
        {
            "number": "22",
            "title": "Основные обязанности работника",
            "content": "Текст статьи 22",
        },
    ]
    
    formatted = format_articles_list(articles)
    
    assert "Найдено статей" in formatted or "найдено" in formatted.lower()
    assert "2" in formatted
    assert "Статья 21" in formatted
    assert "Статья 22" in formatted


def test_format_articles_list_empty():
    """Тест: форматирование пустого списка статей."""
    formatted = format_articles_list([])
    
    assert "не найдены" in formatted.lower() or "не найдено" in formatted.lower()
    assert "❌" in formatted


def test_format_answer_with_articles():
    """Тест: форматирование ответа со статьями."""
    response = {
        "answer": "Согласно статье 21 ТК РФ, работник имеет право...",
        "articles": [
            {
                "number": "21",
                "title": "Основные права работника",
                "content": "Работник имеет право на...",
            }
        ],
        "confidence": 0.95,
    }
    
    formatted = format_answer(response)
    
    assert "Согласно статье 21" in formatted
    # Проверяем наличие секции со статьями
    assert "Найдено статей" in formatted or "найдено" in formatted.lower()
    assert "Статья 21" in formatted
    assert "✅" in formatted  # Высокая уверенность


def test_format_answer_without_articles():
    """Тест: форматирование ответа без статей."""
    response = {
        "answer": "Я могу помочь вам с вопросами по ТК РФ.",
        "articles": [],
        "confidence": 0.7,
    }
    
    formatted = format_answer(response)
    
    assert "Я могу помочь" in formatted
    assert "⚠️" in formatted  # Средняя уверенность


def test_format_answer_low_confidence():
    """Тест: форматирование ответа с низкой уверенностью."""
    response = {
        "answer": "Возможно, вам подойдёт...",
        "articles": [],
        "confidence": 0.4,
    }
    
    formatted = format_answer(response)
    
    assert "❌" in formatted  # Низкая уверенность
    assert "не уверен" in formatted.lower() or "низкая" in formatted.lower()


def test_format_conversation_history():
    """Тест: форматирование истории диалога."""
    conversation = {
        "id": "conv-123",
        "messages": [
            {"role": "user", "content": "Какие права у работника?"},
            {"role": "assistant", "content": "Согласно статье 21..."},
            {"role": "user", "content": "А обязанности?"},
            {"role": "assistant", "content": "Согласно статье 22..."},
        ],
    }
    
    formatted = format_conversation_history(conversation)
    
    assert "История диалога" in formatted or "история" in formatted.lower()
    assert "👤" in formatted  # Пользователь
    assert "🤖" in formatted  # Ассистент
    assert "Какие права у работника" in formatted
    assert "Согласно статье 21" in formatted


def test_format_conversation_history_empty():
    """Тест: форматирование пустой истории."""
    conversation = {
        "id": "conv-123",
        "messages": [],
    }
    
    formatted = format_conversation_history(conversation)
    
    assert "пуста" in formatted.lower() or "пустая" in formatted.lower()
    assert "❌" in formatted


def test_format_conversation_history_max_messages():
    """Тест: ограничение количества сообщений в истории."""
    messages = [
        {"role": "user", "content": f"Вопрос {i}"}
        for i in range(20)
    ]
    conversation = {
        "id": "conv-123",
        "messages": messages,
    }
    
    formatted = format_conversation_history(conversation, max_messages=5)
    
    # Должно быть только 5 последних сообщений
    assert "Вопрос 15" in formatted
    assert "Вопрос 19" in formatted
    assert "Вопрос 0" not in formatted
    assert "последние" in formatted.lower() or "показаны" in formatted.lower()