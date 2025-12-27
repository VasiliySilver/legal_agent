#!/usr/bin/env python
"""Скрипт для запуска Legal Agent Telegram бота."""

import sys
import subprocess
import os


def check_env_file():
    """Проверить наличие .env файла."""
    if not os.path.exists(".env"):
        print("⚠️  Файл .env не найден!")
        print("Создайте .env файл с необходимыми переменными:")
        print("  - BOT_TOKEN")
        print("  - GROQ_API_KEY")
        print("  - POSTGRES_* (или DATABASE_URL)")
        print("\nСм. README.md для деталей")
        return False
    return True


def check_database():
    """Проверить подключение к БД."""
    try:
        subprocess.run(
            ["python", "-m", "src.infrastructure.database", "check"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Не удалось подключиться к БД")
        print("Запустите PostgreSQL:")
        print("  cd docker && docker-compose up -d")
        return False


def run_bot():
    """Запустить Telegram бота."""
    print("🚀 Запуск Legal Agent Telegram бота")
    print()

    # Отключаем прокси для Telegram бота (он использует SOCKS прокси через код)
    proxy_vars = [
        "HTTP_PROXY",
        "http_proxy",
        "HTTPS_PROXY",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
        "NO_PROXY",
        "no_proxy",
    ]
    saved_proxies = {}
    for var in proxy_vars:
        if var in os.environ:
            saved_proxies[var] = os.environ[var]
            del os.environ[var]
            print(f"Unset {var}")

    print("Environment proxies unset")

    try:
        from src.bot.main import main as bot_main
        import asyncio

        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)
    finally:
        # Восстанавливаем прокси
        for var, value in saved_proxies.items():
            os.environ[var] = value


def main():
    """Главная функция."""
    # Проверяем .env
    if not check_env_file():
        sys.exit(1)

    # Проверяем БД
    print("🔍 Проверка подключения к БД...")
    if not check_database():
        print("\n❌ БД недоступна. Исправьте проблему и попробуйте снова.")
        sys.exit(1)

    print("✅ БД доступна\n")

    # Запускаем бота
    run_bot()


if __name__ == "__main__":
    main()
