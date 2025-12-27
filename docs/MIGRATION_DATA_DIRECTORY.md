# Изменения: Перенос данных из scripts/data → data/

## Дата: 10 декабря 2024

## Цель
Правильная организация структуры проекта: данные должны храниться в корневой директории `data/`, а не в `scripts/data/`.

## Внесенные изменения

### 1. Обновлены пути в коде

**src/infrastructure/database.py**
- Изменен путь по умолчанию в функции `load_articles_from_json()`
- Было: `scripts/data/tk_rf_articles.json`
- Стало: `data/tk_rf_articles.json`

**scripts/parser/main.py**
- Обновлен аргумент `--output` по умолчанию
- Было: `../data/tk_rf_articles.json`
- Стало: `../../data/tk_rf_articles.json`
- Обновлен аргумент `--data-dir` по умолчанию
- Было: `../data`
- Стало: `../../data`

### 2. Обновлена документация

**README.md**
- Добавлена секция "4. Загрузка данных (статей ТК РФ)" с двумя вариантами:
  - Вариант А: Использование готового JSON
  - Вариант Б: Парсинг с сайта ConsultantPlus
- Обновлена структура проекта с указанием `data/tk_rf_articles.json`
- Добавлена секция "CLI управление БД" с примерами команд
- Расширено описание таблицы `articles` с полями

**scripts/parser/README.md**
- Обновлены пути в таблице параметров
- Обновлены примеры использования с правильными путями

### 3. Создана структура data/

**data/.gitkeep**
- Создан файл для сохранения пустой директории в git
- Содержит пояснение о назначении папки

**data/README.md**
- Подробная документация о директории данных
- Инструкции по получению данных (парсинг или скачивание)
- Описание структуры JSON файла
- Информация о checkpoints

### 4. Обновлен .gitignore

Добавлены правила игнорирования:
```
# Data files (JSON, checkpoints)
data/*.json
data/checkpoints/
scripts/data/*.json
scripts/data/checkpoints/

# But keep the directory structure
!data/.gitkeep
```

## Как использовать

### Для новых пользователей

1. Клонировать репозиторий
2. Запустить парсер:
   ```bash
   cd scripts/parser
   python main.py
   ```
3. Файл автоматически сохранится в `data/tk_rf_articles.json`
4. Загрузить в БД:
   ```bash
   cd ../..
   python -m src.infrastructure.database load
   ```

### Для существующих пользователей

Если файл уже был в `scripts/data/tk_rf_articles.json`:
```bash
# Переместить файл
mv scripts/data/tk_rf_articles.json data/

# Загрузить в БД (использует новый путь)
python -m src.infrastructure.database load
```

## Проверка

Путь автоматически разрешается относительно `src/infrastructure/database.py`:
```python
json_path = Path(__file__).parent.parent.parent / "data" / "tk_rf_articles.json"
# Результат: /home/user/.../legal_agent/data/tk_rf_articles.json
```

## Обратная совместимость

CLI команда поддерживает явное указание пути:
```bash
# Использовать старый файл
python -m src.infrastructure.database load scripts/data/tk_rf_articles.json

# Использовать новый файл (по умолчанию)
python -m src.infrastructure.database load
```

## Статус миграции данных

✅ Код обновлен
✅ Документация обновлена
✅ .gitignore настроен
✅ Структура data/ создана
✅ README.md в data/ создан
✅ Путь протестирован и работает

## Следующие шаги

- [ ] Переместить существующий `scripts/data/tk_rf_articles.json` → `data/` (если есть)
- [ ] Удалить старую директорию `scripts/data/` (опционально)
- [ ] Обновить CI/CD если используется
- [ ] Обновить инструкции для команды
