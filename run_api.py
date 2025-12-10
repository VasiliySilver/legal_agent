#!/usr/bin/env python
"""Скрипт для запуска Legal Agent API."""

import sys
import subprocess
import os


def check_env_file():
    """Проверить наличие .env файла."""
    if not os.path.exists(".env"):
        print("⚠️  Файл .env не найден!")
        print("Создайте .env файл с необходимыми переменными:")
        print("  - GROQ_API_KEY")
        print("  - POSTGRES_* (или DATABASE_URL)")
        print("\nСм. API_README.md для деталей")
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


def run_api(host="0.0.0.0", port=8000, reload=True):
    """Запустить FastAPI сервер."""
    print(f"🚀 Запуск Legal Agent API на http://{host}:{port}")
    print(f"📚 Документация: http://{host}:{port}/docs")
    print(f"🏥 Health check: http://{host}:{port}/health")
    print()

    cmd = [
        "uvicorn",
        "src.api.main:app",
        f"--host={host}",
        f"--port={port}",
        "--log-level=info",
    ]

    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера...")


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

    # Запускаем API
    run_api()


if __name__ == "__main__":
    main()
