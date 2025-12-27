# Директория данных

Эта папка содержит данные статей Трудового кодекса РФ.

## Файлы

- **tk_rf_articles.json** - основной файл со статьями ТК РФ (~537 статей, ~2-3 MB)
  - Формат: JSON с метаданными и полным текстом статей
  - Не коммитится в git (см. `.gitignore`)

## Получение данных

### Вариант 1: Парсинг с сайта ConsultantPlus

```bash
cd scripts/parser
python main.py

# Результат сохранится в data/tk_rf_articles.json
```

### Вариант 2: Скачать готовый файл

Если есть готовый файл:
1. Скачайте `tk_rf_articles.json`
2. Поместите в эту директорию (`data/`)
3. Загрузите в БД: `python -m src.infrastructure.database load`

## Загрузка в базу данных

После получения JSON файла:

```bash
# Загрузить статьи в PostgreSQL
python -m src.infrastructure.database load

# Или указать путь к файлу
python -m src.infrastructure.database load /path/to/articles.json
```

## Структура JSON

```json
{
  "metadata": {
    "source": "consultant.ru",
    "document": "Трудовой кодекс РФ",
    "total_articles": 537,
    "parsed_at": "2024-12-10T12:00:00"
  },
  "articles": [
    {
      "title": "Статья 1. Цели и задачи трудового законодательства",
      "text": "Целями трудового законодательства...",
      "part": "Часть первая",
      "section": "Раздел I. Общие положения",
      "chapter": "Глава 1. Основные начала трудового законодательства",
      "status": "active",
      "text_length": 450,
      "source": "consultant.ru",
      "source_url": "https://www.consultant.ru/document/...",
      "fetched_at": "2024-12-10T12:00:00"
    }
  ]
}
```

## Checkpoints

При парсинге создаются промежуточные файлы в `data/checkpoints/`:
- `articles_v4_checkpoint_10.json`
- `articles_v4_checkpoint_20.json`
- ...

Это позволяет продолжить парсинг после сбоя.
