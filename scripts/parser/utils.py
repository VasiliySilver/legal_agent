"""
Утилиты для сохранения промежуточных результатов
"""

import json
from pathlib import Path


def save_checkpoint(
    articles: list, failed: list, count: int, data_dir: str = "../../data"
):
    """
    Сохраняет промежуточные результаты парсинга.

    Args:
        articles: Список успешно спарсенных статей
        failed: Список ошибок
        count: Номер чекпоинта (количество обработанных статей)
        data_dir: Путь к директории для сохранения
    """
    checkpoint_dir = Path(data_dir) / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = checkpoint_dir / f"articles_v4_checkpoint_{count}.json"
    checkpoint_file.write_text(
        json.dumps(
            {"count": count, "articles": articles, "failed": failed},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"💾 Чекпоинт сохранен: {checkpoint_file.name}")


def save_final_results(
    articles: list, failed: list, output_file: str = "../../data/tk_rf_articles.json"
):
    """
    Сохраняет финальные результаты в JSON файл.

    Args:
        articles: Список всех статей
        failed: Список ошибок
        output_file: Путь к выходному файлу
    """
    from datetime import datetime

    output_data = {
        "metadata": {
            "source": "ConsultantPlus",
            "url": "https://www.consultant.ru/document/cons_doc_LAW_34683/",
            "document": "Трудовой кодекс РФ",
            "parsed_at": datetime.now().isoformat(),
            "total_articles": len(articles),
            "failed_articles": len(failed),
        },
        "articles": articles,
        "failed": failed,
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"✅ Данные сохранены в: {output_path}")
    print(f"📊 Размер файла: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
