from src.infrastructure.logger import logger
from src.infrastructure.database.session import get_async_session


async def load_articles_from_json(json_path: str = None, clear_existing: bool = True):
    """
    Загрузить статьи ТК РФ из JSON файла в базу данных

    Args:
        json_path: Путь к JSON файлу (по умолчанию data/tk_rf_articles.json)
        clear_existing: Очистить существующие статьи перед загрузкой
    """
    import json
    from pathlib import Path
    from datetime import datetime, timezone
    import re
    import os
    import uuid
    from sqlalchemy import select, delete, func
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from src.infrastructure.models import ArticleModel
    from src.domain.entities import ArticleStatus
    from src.application.services.vector_service import VectorService, VectorBackend
    from src.infrastructure.repositories import ArticleRepository

    # Определяем путь к JSON файлу
    if json_path is None:
        json_path = Path(__file__).parent.parent.parent / "data" / "tk_rf_articles.json"
    else:
        json_path = Path(json_path)

    if not json_path.exists():
        logger.error(f"❌ Файл не найден: {json_path}")
        return

    logger.info(f"📂 Загружаем данные из {json_path}")

    # Загружаем JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles_data = data.get("articles", [])
    metadata = data.get("metadata", {})
    logger.info(f"✅ Загружено статей из файла: {len(articles_data)}")

    if not articles_data:
        logger.error("❌ В JSON файле нет статей для загрузки")
        return

    def parse_article_number(title: str) -> str:
        match = re.search(r"Статья\s+([\d.\-]+)\.?\s*", title)
        if match:
            return match.group(1).rstrip(".")
        return "unknown"

    def convert_article_data(article_data: dict, metadata_obj: dict | None):
        number = parse_article_number(article_data.get("title", ""))

        fetched_at = None
        if article_data.get("fetched_at"):
            try:
                fetched_at = datetime.fromisoformat(article_data["fetched_at"])
            except (ValueError, TypeError):
                fetched_at = datetime.now(timezone.utc)

        status_str = article_data.get("status", "active")
        try:
            status = ArticleStatus(status_str)
        except ValueError:
            status = ArticleStatus.ACTIVE

        return ArticleModel(
            number=number,
            title=article_data.get("title", ""),
            content=article_data.get("text", ""),
            part=article_data.get("part"),
            section=article_data.get("section"),
            chapter=article_data.get("chapter"),
            text_length=article_data.get(
                "text_length", len(article_data.get("text", ""))
            ),
            status=status,
            source=article_data.get("source"),
            source_url=article_data.get("source_url"),
            fetched_at=fetched_at,
            metadata_json=metadata_obj,
        )

    # Преобразуем данные в модели
    articles = []
    for article_data in articles_data:
        try:
            article = convert_article_data(article_data, metadata)
            # Проверка длины полей
            errors = []
            if article.title and len(article.title) > 500:
                errors.append(f"title ({len(article.title)})")
            if article.source_url and len(article.source_url) > 500:
                errors.append(f"source_url ({len(article.source_url)})")
            if article.section and len(article.section) > 200:
                errors.append(f"section ({len(article.section)})")
            if article.chapter and len(article.chapter) > 200:
                errors.append(f"chapter ({len(article.chapter)})")
            if article.source and len(article.source) > 100:
                errors.append(f"source ({len(article.source)})")
            if errors:
                logger.warning(
                    f"❗️ Превышение лимита: {', '.join(errors)} | number={article.number} | title={article.title[:50]}...\n"
                    f"  title: {len(article.title)} | {article.title}\n"
                    f"  source_url: {len(article.source_url) if article.source_url else 0} | {article.source_url}\n"
                    f"  section: {len(article.section) if article.section else 0} | {article.section}\n"
                    f"  chapter: {len(article.chapter) if article.chapter else 0} | {article.chapter}\n"
                    f"  source: {len(article.source) if article.source else 0} | {article.source}\n"
                )
            articles.append(article)
        except Exception as e:
            logger.warning(
                f"⚠️ Ошибка при обработке статьи: {article_data.get('title', 'unknown')}: {e}"
            )
            continue

    logger.info(f"✅ Обработано статей: {len(articles)}")

    # Вставляем пакетами с upsert (Postgres ON CONFLICT)
    async for session in get_async_session():
        try:
            if clear_existing:
                result = await session.execute(select(func.count(ArticleModel.id)))
                count = result.scalar()
                if count and count > 0:
                    logger.info(f"🗑️  Удаляем существующие статьи ({count})...")
                    await session.execute(delete(ArticleModel))
                    await session.commit()

            batch_size = int(os.getenv("LOAD_BATCH_SIZE", "50"))
            total = len(articles)
            logger.info(
                f"💾 Начинаем загрузку {total} статей (пакетами по {batch_size})..."
            )

            for i in range(0, total, batch_size):
                batch = articles[i : i + batch_size]

                # Убираем дубли по number внутри пакета
                values_map = {}
                for a in batch:
                    key = (
                        a.number
                        if a.number and a.number != "unknown"
                        else str(uuid.uuid4())
                    )
                    values_map[key] = {
                        "number": a.number if a.number else key,
                        "title": a.title,
                        "content": a.content,
                        "part": a.part,
                        "section": a.section,
                        "chapter": a.chapter,
                        "text_length": a.text_length,
                        "status": a.status.value
                        if hasattr(a.status, "value")
                        else a.status,
                        "source": a.source,
                        "source_url": a.source_url,
                        "fetched_at": a.fetched_at,
                        "metadata_json": a.metadata_json or {},
                    }

                values = list(values_map.values())

                insert_stmt = pg_insert(ArticleModel).values(values)
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
                logger.info(
                    f"  ✓ Загружено {progress}/{total} статей ({progress * 100 // total}%)"
                )

            # Проверяем результат
            result = await session.execute(select(func.count(ArticleModel.id)))
            total_count = result.scalar()
            logger.info(f"✅ УСПЕШНО! В базе данных теперь {total_count} статей")

            # Построение векторного индекса (если настроено)
            try:
                vector_backend = os.getenv("VECTOR_BACKEND", "").lower()
                if vector_backend in ("faiss", "postgres"):
                    logger.info("🔗 Строим векторный индекс для RAG...")
                    repo = ArticleRepository(session)
                    all_articles = await repo.get_all(limit=5000, offset=0)

                    if vector_backend == "postgres":
                        v_user = os.getenv(
                            "VECTOR_DB_USER", os.getenv("POSTGRES_USER", "postgres")
                        )
                        v_password = os.getenv(
                            "VECTOR_DB_PASSWORD",
                            os.getenv("POSTGRES_PASSWORD", "postgres"),
                        )
                        v_host = os.getenv(
                            "VECTOR_DB_HOST", os.getenv("POSTGRES_HOST", "localhost")
                        )
                        v_port = os.getenv("VECTOR_DB_PORT", "5432")
                        v_name = os.getenv(
                            "VECTOR_DB_NAME",
                            os.getenv("POSTGRES_DB", "legal_agent_vectors"),
                        )
                        conn_str = f"postgresql://{v_user}:{v_password}@{v_host}:{v_port}/{v_name}"
                        vector_service = VectorService(
                            backend=VectorBackend.POSTGRES, connection_string=conn_str
                        )
                    else:
                        vector_service = VectorService(backend=VectorBackend.FAISS)

                    await vector_service.build_index(all_articles)

                    if vector_backend == "faiss":
                        index_path = os.getenv("VECTOR_INDEX_PATH", "data/faiss_index")
                        await vector_service.save(index_path)

                    await vector_service.close()
                    logger.info("✅ Векторный индекс построен и сохранён")

            except Exception as e:
                logger.error(f"Ошибка при построении векторного индекса: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке в БД: {e}")
            await session.rollback()
            raise
