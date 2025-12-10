"""
Конфигурация Telegram бота.
Использует pydantic-settings для загрузки из .env
"""

import re
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseSettings):
    """Конфигурация Telegram бота."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot API
    bot_token: str = Field(
        ...,
        description="Токен Telegram бота от @BotFather",
    )

    # API настройки
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Базовый URL REST API",
    )

    api_timeout: float = Field(
        default=30.0,
        description="Таймаут для HTTP запросов к API (секунды)",
        gt=0,
    )

    # Логирование
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Уровень логирования",
    )

    # Rate Limiting
    rate_limit_per_user: int = Field(
        default=10,
        description="Максимум запросов на пользователя",
        gt=0,
    )

    rate_limit_window: int = Field(
        default=60,
        description="Окно для rate limit (секунды)",
        gt=0,
    )

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """
        Валидация формата токена Telegram бота.
        Формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
        """
        pattern = r"^\d+:[A-Za-z0-9_-]+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Неправильный формат BOT_TOKEN. "
                "Ожидается формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            )
        return v

    @field_validator("api_base_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Валидация URL API."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("API_BASE_URL должен начинаться с http:// или https://")
        return v.rstrip("/")  # Убираем trailing slash

    @property
    def api_v1_url(self) -> str:
        """Полный URL API v1."""
        return f"{self.api_base_url}/api/v1"