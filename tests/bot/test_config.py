"""
Тесты для конфигурации Telegram бота.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.bot.config import BotConfig


def test_bot_config_loads_from_env():
    """Тест: конфигурация загружается из переменных окружения."""
    with patch.dict(
        os.environ,
        {
            "BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "API_BASE_URL": "http://localhost:8000",
        },
    ):
        config = BotConfig()
        assert config.bot_token == "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
        assert config.api_base_url == "http://localhost:8000"


def test_bot_config_has_default_api_url():
    """Тест: API URL имеет значение по умолчанию."""
    with patch.dict(
        os.environ,
        {"BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"},
        clear=True,
    ):
        config = BotConfig()
        assert config.api_base_url == "http://localhost:8000"


def test_bot_config_validates_token_format():
    """Тест: токен бота должен иметь правильный формат."""
    with patch.dict(os.environ, {"BOT_TOKEN": "invalid_token"}, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            BotConfig()
        
        # Проверяем, что ошибка содержит информацию о неправильном формате токена
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "bot_token" in str(errors[0])


def test_bot_config_requires_bot_token():
    """Тест: BOT_TOKEN обязателен."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            BotConfig()
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("bot_token",) for error in errors)


def test_bot_config_api_timeout_default():
    """Тест: API timeout имеет значение по умолчанию."""
    with patch.dict(
        os.environ,
        {"BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"},
        clear=True,
    ):
        config = BotConfig()
        assert config.api_timeout == 30.0


def test_bot_config_api_timeout_custom():
    """Тест: можно задать custom API timeout."""
    with patch.dict(
        os.environ,
        {
            "BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "API_TIMEOUT": "60.0",
        },
    ):
        config = BotConfig()
        assert config.api_timeout == 60.0


def test_bot_config_log_level_default():
    """Тест: уровень логирования по умолчанию."""
    with patch.dict(
        os.environ,
        {"BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"},
        clear=True,
    ):
        config = BotConfig()
        assert config.log_level == "INFO"


def test_bot_config_log_level_custom():
    """Тест: можно задать custom уровень логирования."""
    with patch.dict(
        os.environ,
        {
            "BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "LOG_LEVEL": "DEBUG",
        },
    ):
        config = BotConfig()
        assert config.log_level == "DEBUG"


def test_bot_config_rate_limit_default():
    """Тест: rate limit по умолчанию."""
    with patch.dict(
        os.environ,
        {"BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"},
        clear=True,
    ):
        config = BotConfig()
        assert config.rate_limit_per_user == 10
        assert config.rate_limit_window == 60


def test_bot_config_rate_limit_custom():
    """Тест: можно задать custom rate limit."""
    with patch.dict(
        os.environ,
        {
            "BOT_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "RATE_LIMIT_PER_USER": "20",
            "RATE_LIMIT_WINDOW": "120",
        },
    ):
        config = BotConfig()
        assert config.rate_limit_per_user == 20
        assert config.rate_limit_window == 120