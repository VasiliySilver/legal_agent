"""
CLI для управления базой данных.
"""

import sys
import asyncio

from src.infrastructure.database.check_connection import check_connection
from src.infrastructure.database.close_database import close_database
from src.infrastructure.database.drop_database import drop_database
from src.infrastructure.database.init_database import init_database
from src.infrastructure.load_articles_from_json import load_articles_from_json
from src.infrastructure.database.reset_database import reset_database


async def main():
    if len(sys.argv) < 2:
        print("❌ Не указана команда")
        print("Использование:")
        print("  python -m src.infrastructure.database init    # Создать таблицы")
        print("  python -m src.infrastructure.database drop    # Удалить таблицы")
        print("  python -m src.infrastructure.database reset   # Пересоздать таблицы")
        print("  python -m src.infrastructure.database check   # Проверить подключение")
        print(
            "  python -m src.infrastructure.database load    # Загрузить статьи из JSON"
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        await init_database()
    elif command == "drop":
        confirm = input("⚠️  Удалить ВСЕ данные? (yes/no): ")
        if confirm.lower() == "yes":
            await drop_database()
        else:
            print("Отменено")
    elif command == "reset":
        confirm = input("⚠️  Пересоздать БД и удалить ВСЕ данные? (yes/no): ")
        if confirm.lower() == "yes":
            await reset_database()
        else:
            print("Отменено")
    elif command == "check":
        if await check_connection():
            print("✅ Подключение к БД работает")
        else:
            print("❌ Ошибка подключения к БД")
            sys.exit(1)
    elif command == "load":
        # Опциональный аргумент: путь к JSON файлу
        json_path = sys.argv[2] if len(sys.argv) > 2 else None
        await load_articles_from_json(json_path=json_path, clear_existing=True)
    else:
        print(f"❌ Неизвестная команда: {command}")
        sys.exit(1)

    await close_database()


if __name__ == "__main__":
    # Запускаем async функцию
    asyncio.run(main())
