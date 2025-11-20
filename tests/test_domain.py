"""
Тесты для доменных сущностей
"""
import pytest
from datetime import datetime


def test_article_creation():
    from src.domain.entities import Article
    
    article = Article(
        number="80",
        title="Увольнение",
        content="Текст статьи",
        chapter="Глава 13"
    )
    
    assert article.number == "80"
    assert article.title == "Увольнение"


def test_article_validation_empty_number():
    from src.domain.entities import Article
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        Article(number="", title="Тест", content="Контент", chapter="Глава 1")


def test_legal_query_creation():
    from src.domain.entities import LegalQuery
    
    query = LegalQuery(question="Сколько дней отпуска?", user_id="user123")
    
    assert query.question == "Сколько дней отпуска?"
    assert query.text == "Сколько дней отпуска?"  # test property alias
    assert query.user_id == "user123"
    assert isinstance(query.timestamp, datetime)


def test_legal_query_validation_too_short():
    from src.domain.entities import LegalQuery
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        LegalQuery(question="да", user_id="user123")


def test_legal_answer_creation():
    from src.domain.entities import LegalAnswer, Article
    
    article = Article(number="115", title="Отпуск", content="28 дней", chapter="Глава 19")
    answer = LegalAnswer(
        answer="Ответ агента",
        sources=[115],  # List of article numbers, not Article objects
        confidence=0.95
    )
    
    assert answer.answer == "Ответ агента"
    assert answer.text == "Ответ агента"  # test property alias
    assert len(answer.sources) == 1
    assert answer.sources[0] == 115
    assert answer.confidence == 0.95


def test_legal_conversation_creation():
    from src.domain.entities import LegalConversation
    
    conv = LegalConversation(user_id="user123")
    
    assert conv.user_id == "user123"
    assert len(conv.messages) == 0


def test_legal_conversation_add_message():
    from src.domain.entities import LegalConversation, LegalQuery, LegalAnswer
    
    conv = LegalConversation(user_id="user123")
    query = LegalQuery(question="Вопрос", user_id="user123")
    answer = LegalAnswer(answer="Ответ", sources=[], confidence=0.9)
    
    conv.add_query(query)
    conv.add_answer(answer)
    
    assert len(conv.messages) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
