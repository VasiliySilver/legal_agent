"""
Тесты для билдеров inline клавиатур.
"""

from aiogram.types import InlineKeyboardMarkup

from src.bot.keyboards.builders import (
    build_main_menu,
    build_article_keyboard,
    build_articles_list_keyboard,
    build_conversation_keyboard,
    build_conversations_list_keyboard,
    build_pagination_keyboard,
)


def test_build_main_menu():
    """Тест: построение главного меню."""
    keyboard = build_main_menu()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) > 0

    # Проверяем наличие основных кнопок
    buttons_text = []
    for row in keyboard.inline_keyboard:
        for button in row:
            buttons_text.append(button.text)

    assert "❓ Задать вопрос" in buttons_text
    assert "🔍 Поиск статей" in buttons_text
    assert "📜 История диалогов" in buttons_text
    assert "ℹ️ Помощь" in buttons_text


def test_build_article_keyboard():
    """Тест: клавиатура для одной статьи."""
    keyboard = build_article_keyboard("21")

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем кнопку "Назад" (может быть "Назад к поиску" или просто "Назад")
    buttons_text = []
    for row in keyboard.inline_keyboard:
        for button in row:
            buttons_text.append(button.text)

    # Проверяем что есть хотя бы одна кнопка с "Назад"
    assert any("Назад" in text for text in buttons_text)


def test_build_articles_list_keyboard():
    """Тест: клавиатура со списком статей."""
    articles = [
        {"number": "21", "title": "Основные права работника"},
        {"number": "22", "title": "Основные обязанности работника"},
    ]

    keyboard = build_articles_list_keyboard(articles)

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) >= 2  # Минимум 2 статьи

    # Проверяем, что есть кнопки со статьями
    first_button = keyboard.inline_keyboard[0][0]
    assert "21" in first_button.text


def test_build_articles_list_keyboard_empty():
    """Тест: клавиатура для пустого списка статей."""
    keyboard = build_articles_list_keyboard([])

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Должна быть только кнопка "Назад"
    assert len(keyboard.inline_keyboard) == 1
    back_button = keyboard.inline_keyboard[0][0]
    assert "Назад" in back_button.text


def test_build_articles_list_keyboard_with_pagination():
    """Тест: клавиатура статей с пагинацией."""
    articles = [{"number": str(i), "title": f"Статья {i}"} for i in range(20)]

    keyboard = build_articles_list_keyboard(
        articles,
        current_page=2,
        total_pages=4,
    )

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем наличие кнопок навигации
    last_row = keyboard.inline_keyboard[-2]  # Предпоследняя строка (перед "Назад")

    # Должны быть кнопки ◀️ и ▶️
    nav_buttons_text = [btn.text for btn in last_row]
    assert any("◀️" in text or "Назад" in text for text in nav_buttons_text)
    assert any("▶️" in text or "Вперёд" in text for text in nav_buttons_text)


def test_build_conversation_keyboard():
    """Тест: клавиатура для диалога."""
    keyboard = build_conversation_keyboard("conv-123")

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем наличие кнопок
    buttons_text = []
    for row in keyboard.inline_keyboard:
        for button in row:
            buttons_text.append(button.text)

    assert any("Продолжить" in text for text in buttons_text)
    assert any("Удалить" in text for text in buttons_text)
    assert any("Назад" in text for text in buttons_text)


def test_build_conversations_list_keyboard():
    """Тест: клавиатура со списком диалогов."""
    conversations = [
        {"id": "conv-1", "created_at": "2025-12-10T10:00:00Z"},
        {"id": "conv-2", "created_at": "2025-12-10T11:00:00Z"},
    ]

    keyboard = build_conversations_list_keyboard(conversations)

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) >= 2

    # Проверяем кнопку "Новый диалог"
    buttons_text = []
    for row in keyboard.inline_keyboard:
        for button in row:
            buttons_text.append(button.text)

    assert any("Новый диалог" in text for text in buttons_text)


def test_build_conversations_list_keyboard_empty():
    """Тест: клавиатура для пустого списка диалогов."""
    keyboard = build_conversations_list_keyboard([])

    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Должны быть кнопки "Новый диалог" и "Назад"
    assert len(keyboard.inline_keyboard) == 2


def test_build_pagination_keyboard():
    """Тест: построение кнопок пагинации."""
    keyboard = build_pagination_keyboard(
        current_page=2,
        total_pages=5,
        callback_prefix="article",
    )

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 1  # Одна строка с навигацией

    row = keyboard.inline_keyboard[0]
    assert len(row) >= 2  # Минимум 2 кнопки

    # Проверяем callback data
    for button in row:
        assert button.callback_data is not None


def test_build_pagination_keyboard_first_page():
    """Тест: пагинация на первой странице."""
    keyboard = build_pagination_keyboard(
        current_page=1,
        total_pages=5,
        callback_prefix="article",
    )

    row = keyboard.inline_keyboard[0]

    # На первой странице не должно быть кнопки "Назад"
    buttons_text = [btn.text for btn in row]
    assert not any("◀️" in text for text in buttons_text)


def test_build_pagination_keyboard_last_page():
    """Тест: пагинация на последней странице."""
    keyboard = build_pagination_keyboard(
        current_page=5,
        total_pages=5,
        callback_prefix="article",
    )

    row = keyboard.inline_keyboard[0]

    # На последней странице не должно быть кнопки "Вперёд"
    buttons_text = [btn.text for btn in row]
    assert not any("▶️" in text for text in buttons_text)


def test_build_pagination_keyboard_single_page():
    """Тест: пагинация для одной страницы."""
    keyboard = build_pagination_keyboard(
        current_page=1,
        total_pages=1,
        callback_prefix="article",
    )

    # Для одной страницы клавиатура должна быть пустой
    assert len(keyboard.inline_keyboard) == 0


def test_keyboard_buttons_have_callback_data():
    """Тест: все кнопки имеют callback_data."""
    keyboard = build_main_menu()

    for row in keyboard.inline_keyboard:
        for button in row:
            assert button.callback_data is not None
            assert len(button.callback_data) > 0
            assert len(button.callback_data.encode("utf-8")) <= 64  # Лимит Telegram
