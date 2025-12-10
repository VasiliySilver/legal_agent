"""
Telegram Bot для Legal Agent.
Обеспечивает доступ к юридическим консультациям через Telegram.
"""

from src.bot.api_client import LegalAgentAPIClient
from src.bot.config import BotConfig

__all__ = [
    "BotConfig",
    "LegalAgentAPIClient",
]