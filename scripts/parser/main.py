"""
Главный модуль для парсинга Трудового кодекса РФ.

Использование:
    python main.py                 # Парсит все статьи
    python main.py --limit 10      # Парсит первые 10 статей (тест)
    python main.py --start-from 50 # Продолжить с 50-й статьи
"""

import asyncio
import argparse
from tqdm.asyncio import tqdm

from fetcher import fetch_article_links
from hierarchy import parse_tk_rf_hierarchy
from article_parser import fetch_article_v4
from utils import save_checkpoint, save_final_results


async def fetch_article_with_semaphore(
    semaphore: asyncio.Semaphore,
    article_link: dict,
    index: int,
    hierarchy_map: dict,
) -> tuple[int, dict | None, dict | None]:
    """
    Парсит одну статью с ограничением через семафор.

    Args:
        semaphore: Семафор для ограничения параллельных запросов
        article_link: Данные о ссылке на статью
        index: Индекс статьи в общем списке
        hierarchy_map: Маппинг иерархии

    Returns:
        tuple: (index, result or None, error_dict or None)
    """
    async with semaphore:  # Ограничиваем количество одновременных запросов
        try:
            result = await fetch_article_v4(
                article_link["href"], article_link["text"], hierarchy_map
            )

            if result and result["text_length"] > 50:
                return (index, result, None)
            elif result:
                # Текст короткий
                error = {
                    "index": index,
                    "title": article_link["text"],
                    "url": article_link["href"],
                    "reason": f"Текст короткий: {result['text_length']} символов",
                }
                return (index, None, error)
            else:
                # Ошибка загрузки
                error = {
                    "index": index,
                    "title": article_link["text"],
                    "url": article_link["href"],
                    "reason": "Ошибка загрузки",
                }
                return (index, None, error)

        except Exception as e:
            error = {
                "index": index,
                "title": article_link["text"],
                "url": article_link["href"],
                "reason": str(e),
            }
            return (index, None, error)


async def parse_all_articles(
    article_links: list[dict],
    hierarchy_map: dict,
    start_from: int = 0,
    limit: int | None = None,
    checkpoint_interval: int = 10,
    batch_size: int = 5,
    data_dir: str = "../data",
) -> tuple[list[dict], list[dict]]:
    """
    Парсит все статьи с параллельной обработкой батчами.

    Args:
        article_links: Список ссылок на статьи
        hierarchy_map: Маппинг номер статьи → иерархия
        start_from: С какой статьи начать (для продолжения после ошибки)
        limit: Ограничение количества статей (для тестирования)
        checkpoint_interval: Интервал сохранения чекпоинтов
        batch_size: Количество статей для параллельной обработки (рекомендуется 3-5)
        data_dir: Путь к директории для сохранения

    Returns:
        tuple: (список успешно спарсенных статей, список ошибок)
    """
    all_articles = []
    failed_articles = []

    # Применяем limit если указан
    if limit:
        article_links = article_links[:limit]

    # Обрезаем до start_from
    articles_to_process = article_links[start_from:]
    total_count = len(article_links)

    print(
        f"🚀 Начинаем ПАРАЛЛЕЛЬНЫЙ парсинг {len(articles_to_process)} статей (v4 - с метаданными)..."
    )
    print(f"⚡ Размер батча: {batch_size} статей одновременно (через семафор)")
    print(
        f"⏱️  Примерное время: ~{len(articles_to_process) * 30 // 60 // batch_size} минут\n"
    )

    # Создаём семафор для ограничения одновременных запросов
    semaphore = asyncio.Semaphore(batch_size)

    # Разбиваем на батчи для checkpoint'ов
    with tqdm(
        total=len(articles_to_process), desc="Парсинг статей v4", initial=0
    ) as pbar:
        for batch_start in range(0, len(articles_to_process), checkpoint_interval):
            batch_end = min(batch_start + checkpoint_interval, len(articles_to_process))
            batch = articles_to_process[batch_start:batch_end]

            # Используем TaskGroup для лучшей обработки ошибок
            try:
                async with asyncio.TaskGroup() as tg:
                    tasks = []
                    for i, article_link in enumerate(batch):
                        task = tg.create_task(
                            fetch_article_with_semaphore(
                                semaphore,
                                article_link,
                                start_from + batch_start + i,
                                hierarchy_map,
                            )
                        )
                        tasks.append(task)

                # TaskGroup автоматически ждёт все задачи
                # Обрабатываем результаты
                for task in tasks:
                    try:
                        index, article, error = task.result()
                        if article:
                            all_articles.append(article)
                        if error:
                            failed_articles.append(error)
                    except Exception as e:
                        # Обработка неожиданных ошибок
                        failed_articles.append(
                            {
                                "index": -1,
                                "title": "Unknown",
                                "url": "Unknown",
                                "reason": f"Task error: {str(e)}",
                            }
                        )
                    finally:
                        pbar.update(1)

            except* Exception as eg:
                # TaskGroup собирает все исключения в ExceptionGroup
                # Обрабатываем каждое
                for exc in eg.exceptions:
                    failed_articles.append(
                        {
                            "index": -1,
                            "title": "Unknown",
                            "url": "Unknown",
                            "reason": f"Batch error: {str(exc)}",
                        }
                    )
                # Продолжаем со следующим батчем

            # Сохраняем checkpoint после каждого батча
            current_count = start_from + batch_end
            if current_count % checkpoint_interval == 0 or batch_end == len(
                articles_to_process
            ):
                save_checkpoint(all_articles, failed_articles, current_count, data_dir)

    return all_articles, failed_articles


async def main():
    """Главная функция парсера."""
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Парсер Трудового кодекса РФ")
    parser.add_argument(
        "--limit",
        type=int,
        help="Ограничить количество статей (для тестирования)",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Начать с указанной статьи (для продолжения)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../../data/tk_rf_articles.json",
        help="Путь к выходному файлу",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="../../data",
        help="Директория для сохранения промежуточных результатов",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=10,
        help="Интервал сохранения чекпоинтов (каждые N статей)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Количество статей для параллельной обработки (рекомендуется 3-7)",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("🎭 Парсер ТК РФ через Playwright (⚡ ПАРАЛЛЕЛЬНЫЙ)")
    print("=" * 80)
    print()

    # Шаг 1: Загружаем список статей
    print("📥 Шаг 1: Загружаем список статей...")
    html, article_links = await fetch_article_links()
    print(f"✅ Найдено статей: {len(article_links)}")
    print(f"📋 Первые 3: {', '.join([a['text'][:20] for a in article_links[:3]])}\n")

    # Шаг 2: Парсим иерархию
    print("🗂️  Шаг 2: Парсим иерархию (Часть → Раздел → Глава)...")
    hierarchy_map = parse_tk_rf_hierarchy(html)
    print(f"✅ Извлечено иерархий для {len(hierarchy_map)} статей\n")

    # Шаг 3: Парсим статьи
    print("🚀 Шаг 3: Парсим статьи с Playwright...")
    all_articles, failed_articles = await parse_all_articles(
        article_links,
        hierarchy_map,
        start_from=args.start_from,
        limit=args.limit,
        checkpoint_interval=args.checkpoint_interval,
        batch_size=args.batch_size,
        data_dir=args.data_dir,
    )

    print(f"\n{'=' * 80}")
    print("✅ Парсинг завершен!")
    print(f"{'=' * 80}\n")
    print(f"📊 Успешно спарсено: {len(all_articles)} статей")
    print(f"❌ Ошибок: {len(failed_articles)} статей")

    if failed_articles:
        print("\n⚠️  Статьи с ошибками:")
        for item in failed_articles[:10]:
            print(f"  - {item['title']}: {item['reason']}")

    # Шаг 4: Сохраняем результаты
    print("\n💾 Шаг 4: Сохраняем финальные результаты...")
    save_final_results(all_articles, failed_articles, args.output)

    print("\n✨ Готово!")


if __name__ == "__main__":
    asyncio.run(main())
