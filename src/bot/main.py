"""
Точка входа для Telegram бота.
Инициализация и запуск всех компонентов.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.api_client import LegalAgentAPIClient
from src.bot.config import BotConfig
from src.bot.handlers import (
    articles_router,
    conversations_router,
    errors_router,
    questions_router,
    start_router,
)
from src.bot.middlewares import (
    ApiClientMiddleware,
    LoggingMiddleware,
    ThrottlingMiddleware,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Главная функция запуска бота.
    """
    # Загружаем конфигурацию
    logger.info("Loading configuration...")
    config = BotConfig()

    # Устанавливаем уровень логирования из конфига
    logging.getLogger().setLevel(config.log_level)

    # Инициализируем бот с дефолтной сессией
    logger.info("Initializing bot...")
    bot = Bot(
        token=config.bot_token,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    # Инициализируем диспетчер с FSM storage
    dp = Dispatcher(storage=MemoryStorage())

    # Инициализируем API клиент
    logger.info(f"Initializing API client (URL: {config.api_base_url})...")
    api_client = LegalAgentAPIClient(config)

    # Регистрируем middlewares
    logger.info("Registering middlewares...")

    # Middleware логирования (первым - для логирования всех событий)
    dp.update.middleware(LoggingMiddleware())

    # Middleware rate limiting
    dp.update.middleware(
        ThrottlingMiddleware(
            rate_limit=config.rate_limit_per_user,
            window=config.rate_limit_window,
        )
    )

    # Middleware для инъекции API клиента
    dp.update.middleware(ApiClientMiddleware(api_client))

    # Регистрируем роутеры (порядок важен!)
    logger.info("Registering routers...")
    dp.include_router(start_router)
    dp.include_router(questions_router)
    dp.include_router(articles_router)
    dp.include_router(conversations_router)
    dp.include_router(errors_router)  # Errors router последним

    # Проверяем подключение к Telegram
    try:
        logger.info("Testing Telegram API connection...")
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot connected: @{bot_info.username} ({bot_info.first_name})")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Telegram API: {e}")
        logger.error("Please check your BOT_TOKEN and network connection")
        await api_client.close()
        await bot.session.close()
        sys.exit(1)

    # Запускаем бота
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        # Закрываем соединения
        logger.info("Shutting down...")
        await api_client.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
