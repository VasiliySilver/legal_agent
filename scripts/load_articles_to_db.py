"""
Скрипт для загрузки статей ТК РФ из JSON файла в базу данных
Использует асинхронную загрузку с batch-вставкой для оптимизации
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict

from src.infrastructure.database.session import get_async_session

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.load_articles_from_json import load_articles_from_json

from sqlalchemy import select, delete, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
import uuid
from src.infrastructure.database.init_database import init_database
from src.infrastructure.models import ArticleModel
from src.domain.entities import ArticleStatus


async def load_json_file(file_path: Path) -> Dict:
    """
    Загрузить данные из JSON файла

    Args:
        file_path: Путь к JSON файлу

    Returns:
        Dict: Данные из файла
    """
    print(f"📂 Загружаем данные из {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✅ Загружено статей: {len(data.get('articles', []))}")
    return data


def parse_article_number(title: str) -> str:
    """
    Извлечь номер статьи из заголовка

    Args:
        title: Заголовок статьи (например, "ТК РФ Статья 1. Цели и задачи...")

    Returns:
        str: Номер статьи (например, "1")
    """
    # Извлекаем номер статьи из заголовка
    if "Статья" in title:
        parts = title.split("Статья")
        if len(parts) > 1:
            number_part = parts[1].split(".")[0].strip()
            return number_part
    return "unknown"


def convert_article_data(article_data: Dict, metadata: Dict | None) -> ArticleModel:
    """
    Преобразовать данные из JSON в модель ArticleModel

    Args:
        article_data: Словарь с данными статьи из JSON

    Returns:
        ArticleModel: ORM модель статьи
    """
    # Извлекаем номер статьи из заголовка
    number = parse_article_number(article_data.get("title", ""))

    # Парсим дату
    fetched_at = None
    if article_data.get("fetched_at"):
        try:
            fetched_at = datetime.fromisoformat(article_data["fetched_at"])
        except (ValueError, TypeError):
            fetched_at = datetime.now(UTC)

    # Определяем статус статьи
    status_str = article_data.get("status", "active")
    try:
        status = ArticleStatus(status_str)
    except ValueError:
        status = ArticleStatus.ACTIVE

    # Создаем модель
    article_model = ArticleModel(
        number=number,
        title=article_data.get("title", ""),
        content=article_data.get("text", ""),
        part=article_data.get("part"),
        section=article_data.get("section"),
        chapter=article_data.get("chapter"),
        text_length=article_data.get("text_length", len(article_data.get("text", ""))),
        status=status,
        source=article_data.get("source"),
        source_url=article_data.get("source_url"),
        fetched_at=fetched_at,
        metadata_json=metadata,
    )

    return article_model


async def clear_existing_articles(session):
    """
    Очистить существующие статьи из базы данных

    Args:
        session: Асинхронная сессия БД
    """
    print("🗑️  Удаляем существующие статьи...")
    result = await session.execute(select(func.count(ArticleModel.id)))
    count = result.scalar()

    if count > 0:
        await session.execute(delete(ArticleModel))
        await session.commit()
        print(f"✅ Удалено статей: {count}")
    else:
        print("ℹ️  База данных пуста")


async def insert_articles_batch(
    session, articles: List[ArticleModel], batch_size: int = 50
):
    """
    Вставить статьи в базу данных пакетами

    Args:
        session: Асинхронная сессия БД
        articles: Список моделей статей
        batch_size: Размер пакета для вставки
    """
    total = len(articles)
    print(f"💾 Начинаем загрузку {total} статей (пакетами по {batch_size})...")

    for i in range(0, total, batch_size):
        batch = articles[i : i + batch_size]

        # Подготавливаем данные для вставки/обновления
        # Убираем дубликаты по полю `number` внутри пакета — если `number` отсутствует,
        # генерируем временный уникальный ключ, чтобы избежать конфликта ON CONFLICT внутри одного запроса.
        values_map = {}
        for a in batch:
            key = a.number if a.number and a.number != "unknown" else str(uuid.uuid4())
            values_map[key] = {
                "number": a.number if a.number else key,
                "title": a.title,
                "content": a.content,
                "part": a.part,
                "section": a.section,
                "chapter": a.chapter,
                "text_length": a.text_length,
                "status": a.status.value if hasattr(a.status, "value") else a.status,
                "source": a.source,
                "source_url": a.source_url,
                "fetched_at": a.fetched_at,
                "metadata_json": a.metadata_json or {},
            }

        values = list(values_map.values())

        insert_stmt = pg_insert(ArticleModel).values(values)

        # On conflict update: обновляем все релевантные поля (кроме PK)
        update_dict = {
            "title": insert_stmt.excluded.title,
            "content": insert_stmt.excluded.content,
            "part": insert_stmt.excluded.part,
            "section": insert_stmt.excluded.section,
            "chapter": insert_stmt.excluded.chapter,
            "text_length": insert_stmt.excluded.text_length,
            "status": insert_stmt.excluded.status,
            "source": insert_stmt.excluded.source,
            "source_url": insert_stmt.excluded.source_url,
            "fetched_at": insert_stmt.excluded.fetched_at,
            "metadata_json": insert_stmt.excluded.metadata_json,
            "updated_at": func.now(),
        }

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["number"], set_=update_dict
        )

        await session.execute(upsert_stmt)
        await session.commit()

        progress = min(i + batch_size, total)
        print(f"  ✓ Загружено {progress}/{total} статей ({progress * 100 // total}%)")

    print("✅ Все статьи успешно загружены!")


async def load_articles_to_database(
    json_path: Path, clear_existing: bool = True, batch_size: int = 50
):
    """
    Загрузить статьи из JSON файла в базу данных

    Args:
        json_path: Путь к JSON файлу
        clear_existing: Очистить существующие данные перед загрузкой
        batch_size: Размер пакета для batch-вставки
    """
    print("=" * 70)
    print("🚀 ЗАГРУЗКА СТАТЕЙ ТК РФ В БАЗУ ДАННЫХ")
    print("=" * 70)

    # Проверяем существование файла
    if not json_path.exists():
        print(f"❌ Файл не найден: {json_path}")
        return

    # Загружаем данные из JSON
    data = await load_json_file(json_path)
    articles_data = data.get("articles", [])
    metadata = data.get("metadata", {})

    if not articles_data:
        print("❌ В JSON файле нет статей для загрузки")
        return

    # Создаем таблицы если их нет
    print("\n📋 Создаем таблицы в БД (если их нет)...")
    await init_database()

    # Преобразуем данные в модели
    print("\n🔄 Преобразуем данные в модели...")
    articles = []
    for article_data in articles_data:
        try:
            article_model = convert_article_data(article_data, metadata)
            articles.append(article_model)
        except Exception as e:
            print(
                f"⚠️  Ошибка при обработке статьи: {article_data.get('title', 'unknown')}"
            )
            print(f"   {str(e)}")
            continue

    print(f"✅ Обработано статей: {len(articles)}")

    # Загружаем в базу данных
    async for session in get_async_session():
        try:
            # Очищаем существующие данные (опционально)
            if clear_existing:
                await clear_existing_articles(session)

            # Вставляем новые данные
            print()
            await insert_articles_batch(session, articles, batch_size)

            # Проверяем результат
            result = await session.execute(select(func.count(ArticleModel.id)))
            total_count = result.scalar()

            print("\n" + "=" * 70)
            print(f"✅ УСПЕШНО! В базе данных теперь {total_count} статей")
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Ошибка при загрузке в БД: {e}")
            await session.rollback()
            raise


async def main():
    """Delegate to `src.infrastructure.database.load_articles_from_json` to reuse central loader."""
    json_file = project_root / "data" / "tk_rf_articles.json"
    try:
        await load_articles_from_json(json_path=str(json_file), clear_existing=True)
    except KeyboardInterrupt:
        print("\n⚠️  Загрузка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
