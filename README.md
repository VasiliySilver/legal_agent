# 🏛️ Legal Agent - Юридический ассистент по Трудовому Кодексу РФ

AI-агент для консультаций по Трудовому Кодексу РФ с использованием RAG (Retrieval-Augmented Generation).

## 📋 Описание

Legal Agent - это интеллектуальный ассистент, который помогает найти ответы на вопросы по законодательству России. Система использует:

- **RAG архитектуру** для точных ответов на основе статей РФ
- **Векторный поиск** для семантического понимания вопросов
- **LLM (Groq API)** для генерации человекопонятных ответов
- **PostgreSQL** для хранения данных и истории диалогов

## 🚀 Быстрый старт

### 1. Клонирование и установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd legal_agent

# Установка зависимостей (требуется Python 3.12+)
uv sync
```

### 2. Настройка окружения

Создайте `.env` файл в корне проекта: `cp .env.example .env`

Docker-specific env settings можно хранить в `docker/.env` и использовать только для compose `cp docker/.env.example .env`.

### 3. Запуск базы данных

```bash
cd docker
docker compose up -d
cd ..
```env
# Groq API для LLM
GROQ_API_KEY=your_groq_api_key_here

# PostgreSQL - основная БД
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legal_agent

# PostgreSQL - векторная БД
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=postgres
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5433
VECTOR_DB_NAME=legal_agent_vectors

# Опционально: прокси (если требуется)
GROQ_PROXY=socks5://127.0.0.1:12334/
```
# Инициализация схемы БД
python -m src.infrastructure.database init
```

### 3.1. Построение векторного индекса для RAG

После загрузки статей в основную БД можно автоматически построить векторный индекс (FAISS или PostgreSQL+pgvector) для использования RAG.

- Переменные окружения:
  - `VECTOR_BACKEND` — `faiss` или `postgres` (если не задано, индекс не будет строиться)
  - Для `postgres` используйте `VECTOR_DB_USER`, `VECTOR_DB_PASSWORD`, `VECTOR_DB_HOST`, `VECTOR_DB_PORT`, `VECTOR_DB_NAME` (по умолчанию берутся `POSTGRES_*`)
  - Для `faiss` можно указать `VECTOR_INDEX_PATH` — путь для сохранения индекса (по умолчанию `data/faiss_index`)

- Пример (FAISS):

```bash
VECTOR_BACKEND=faiss VECTOR_INDEX_PATH=data/faiss_index python -m src.infrastructure.database load
```

- Пример (Postgres pgvector):

```bash
VECTOR_BACKEND=postgres \
  VECTOR_DB_HOST=localhost VECTOR_DB_PORT=5433 VECTOR_DB_NAME=legal_agent_vectors \
  python -m src.infrastructure.database load
```

Загрузка статей через `python -m src.infrastructure.database load` автоматически построит индекс, если `VECTOR_BACKEND` настроен.


### 4. Загрузка данных (статей ТК РФ)

**Вариант А: Использование готового JSON файла**
```bash
# Загрузить готовые статьи из JSON в базу данных
python -m src.infrastructure.database load

# Или указать путь к своему файлу
python -m src.infrastructure.database load /path/to/articles.json
```

**Вариант Б: Парсинг с сайта ConsultantPlus**
```bash
# Установить зависимости для парсера
pip install playwright httpx beautifulsoup4
playwright install chromium

# Запустить парсер
cd scripts/parser
python main.py

# Результат сохранится в data/tk_rf_articles.json
# Затем загрузить в БД:
cd ../..
python -m src.infrastructure.database load
```

> 💡 **Примечание**: Парсинг всех ~537 статей занимает около 30-40 минут.
> Для тестирования можно ограничить количество: `python main.py --limit 10`

### 5. Запуск API

```bash
# Простой запуск с проверками
python run_api.py

# Или напрямую через uvicorn
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: http://localhost:8000

## 📚 Документация

- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

Подробная документация:
- [API README](docs/api/API_README.md) - полное описание API
- [Quick Start](QUICKSTART_API.md) - быстрый старт
- [Docker Setup](docker/README.md) - настройка БД
- [pgvector Setup](docker/PGVECTOR_SETUP.md) - векторный поиск
- [Parser README](scripts/parser/README.md) - парсер статей ТК РФ

## 🏗️ Архитектура

Проект следует **Clean Architecture** (DDD):

```
legal_agent/
├── data/                    # Данные проекта
│   └── tk_rf_articles.json # Статьи ТК РФ (537 статей)
│
├── src/                    # Исходный код
│   ├── domain/            # Бизнес-логика (entities)
│   │   └── entities/     # Article, Conversation, Message
│   │
│   ├── application/       # Use cases и сервисы
│   │   ├── services/     # LLM, Vector, Embedding services
│   │   └── use_cases/    # Бизнес-логика приложения
│   │
├── infrastructure/      # Внешние зависимости
│   ├── database.py     # Подключение к БД
│   ├── models.py       # SQLAlchemy модели
│   └── repositories/   # Работа с БД
│
└── api/                # FastAPI REST API
    ├── routes/         # HTTP endpoints
    ├── schemas/        # Pydantic модели
    └── dependencies.py # Dependency Injection
```

### Основные компоненты

- **FastAPI** - REST API
- **PostgreSQL** - хранение статей и диалогов
- **pgvector** - векторный поиск (опционально)
- **FAISS** - векторный поиск (по умолчанию)
- **Groq API** - LLM для генерации ответов
- **sentence-transformers** - эмбеддинги для поиска

## 🔌 Основные API endpoints

### Вопросы

```bash
# Быстрый ответ без сохранения истории
curl -X POST http://localhost:8000/api/v1/questions/quick \
  -H "Content-Type: application/json" \
  -d '{"question": "Как уволиться по собственному желанию?"}'

# Вопрос с сохранением истории
curl -X POST http://localhost:8000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Какой срок отработки?",
    "user_id": "user123",
    "conversation_id": "conv456"
  }'
```

### Поиск статей

```bash
# Поиск по номеру
curl "http://localhost:8000/api/v1/articles?query=80&strategy=by_number"

# Семантический поиск
curl "http://localhost:8000/api/v1/articles?query=увольнение&strategy=semantic&limit=5"

# Получить статью по номеру
curl "http://localhost:8000/api/v1/articles/80"
```

### Диалоги

```bash
# Список диалогов
curl "http://localhost:8000/api/v1/conversations?user_id=user123"

# Создать диалог
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "title": "Вопросы по увольнению"}'
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Только API тесты
pytest tests/api/

# С покрытием кода
pytest --cov=src tests/

# Подробный вывод
pytest -v -s tests/
```

## 📊 Структура БД

### Основная БД (legal_agent)

- **articles** - статьи Трудового Кодекса РФ
  - `number` - номер статьи (например, "80", "19.1")
  - `title` - полное название статьи
  - `content` - текст статьи
  - `part`, `section`, `chapter` - иерархия в кодексе
  - `status` - статус статьи (ACTIVE, ABOLISHED, SUSPENDED)
  - `source`, `source_url` - источник данных
  - `fetched_at` - дата получения данных

- **conversations** - диалоги пользователей
- **messages** - сообщения в диалогах

### Векторная БД (legal_agent_vectors)

- **article_vectors** - векторные эмбеддинги статей для семантического поиска

### CLI управление БД

```bash
# Создать таблицы
python -m src.infrastructure.database init

# Удалить все таблицы (⚠️ осторожно!)
python -m src.infrastructure.database drop

# Пересоздать БД (drop + init)
python -m src.infrastructure.database reset

# Проверить подключение
python -m src.infrastructure.database check

# Загрузить статьи из JSON
python -m src.infrastructure.database load
python -m src.infrastructure.database load /path/to/custom.json
```

## 🛠️ Разработка

### Jupyter Notebooks

В проекте есть ноутбуки для экспериментов:

- [`notebooks/research.ipynb`](notebooks/research.ipynb) - прототип RAG системы
- [`notebooks/tk_rf_parser.ipynb`](notebooks/tk_rf_parser.ipynb) - парсер статей ТК РФ
- [`notebooks/data_generation.ipynb`](notebooks/data_generation.ipynb) - генерация данных
- [`notebooks/raft_new.ipynb`](notebooks/raft_new.ipynb) - эксперименты с RAFT

### Инструменты

```bash
# Форматирование кода
black src/ tests/

# Линтер
ruff check src/ tests/

# Сортировка импортов
isort src/ tests/

# Проверка типов
mypy src/
```

## 📦 Данные

Статьи Трудового Кодекса РФ:

- **Источник**: https://www.consultant.ru/document/cons_doc_LAW_34683/
- **Формат**: JSON с метаданными
- **Файл**: [`data/tk_rf_articles.json`](data/tk_rf_articles.json)

Парсинг выполняется через Playwright для рендеринга JavaScript.

## 🔐 Безопасность

⚠️ **Для production:**

1. Измените пароли БД в `docker/.env`
2. Настройте CORS для конкретных доменов
3. Добавьте аутентификацию (JWT)
4. Добавьте rate limiting
5. Используйте HTTPS

## 🐛 Troubleshooting

### БД не запускается

```bash
# Проверить статус контейнеров
docker compose ps

# Посмотреть логи
docker compose logs postgres postgres_vector

# Пересоздать контейнеры
docker compose down -v
docker compose up -d
```

### Import errors

```bash
# Переустановить зависимости
uv sync

# Проверить версию Python (должна быть 3.12+)
python --version
```

### GROQ_API_KEY не найден

Убедитесь, что `.env` файл существует и содержит:

```env
GROQ_API_KEY=your_api_key_here
```

## 📝 TODO

- [ ] Добавить JWT аутентификацию
- [ ] Добавить rate limiting
- [ ] Добавить кеширование ответов (Redis)
- [ ] WebSocket для streaming ответов
- [ ] Telegram бот интерфейс
- [ ] Метрики (Prometheus)
- [ ] CI/CD pipeline
- [ ] Docker образ для API

## 🤝 Contributing

Проект использует **Commitizen** для conventional commits и **Gitflow** для управления ветками.

### Workflow

1. Fork проекта
2. Клонируйте свой fork:
   ```bash
   git clone https://github.com/your-username/legal_agent.git
   cd legal_agent
   ```

3. Создайте feature branch от `develop` с номером задачи:
   ```bash
   git checkout develop
   git pull origin develop

   # Gitflow с номером issue
   git flow feature start #42
   # или вручную:
   git checkout -b feature/#42 develop
   ```

4. Внесите изменения и используйте **Commitizen** для коммитов:
   ```bash
   # Добавьте изменения
   git add .

   # Commitizen интерактивный коммит
   cz commit
   # или: cz c

   # Следуйте подсказкам:
   # - Выберите тип: feat, fix, docs, style, refactor, test, chore
   # - Укажите scope (опционально): api, database, parser, etc.
   # - Напишите краткое описание с номером задачи: #42 - add new feature
   # - Добавьте подробное описание (опционально)
   # - Укажите breaking changes (если есть)
   ```

5. Push feature branch:
   ```bash
   git push origin feature/#42
   ```

6. Откройте Pull Request в `develop` ветку основного репозитория

### Формат коммитов

Все коммиты должны содержать **номер задачи** в описании:

```
<type>(<scope>): #<issue> - <description>

[optional body]

[optional footer]
```

**Примеры:**

```bash
feat(api): #42 - add JWT authentication endpoint
fix(database): #43 - resolve connection pool timeout
docs(readme): #44 - update installation instructions
refactor(services): #45 - extract LLM client to separate class
test(api): #46 - add integration tests for questions endpoint
```

### Типы коммитов (Conventional Commits)

- **feat**: новая функциональность
  ```bash
  feat(api): #6 - add REST API endpoints and documentation
  ```
- **fix**: исправление бага
  ```bash
  fix(database): #12 - resolve connection pool timeout
  ```
- **docs**: изменения в документации
  ```bash
  docs(api): #6 - add docs, update .gitignore
  ```
- **style**: форматирование кода
  ```bash
  style(api): #8 - format code with black
  ```
- **refactor**: рефакторинг кода
  ```bash
  refactor(core): #6 - update use cases, services, domain models
  ```
- **test**: добавление/изменение тестов
  ```bash
  test(use_cases): #5 - add tests for answer legal question
  ```
- **build**: изменения в сборке/зависимостях
  ```bash
  build(deps): #6 - update dependencies and docker configuration
  ```
- **chore**: обновление конфигурации, скриптов
  ```bash
  chore(scripts): #6 - add utility scripts for project management
  ```

### Gitflow ветки

- `main` - production-ready код
- `develop` - основная ветка разработки
- `feature/#<N>` - новые функции (например, `feature/#42`)
- `release/<version>` - подготовка релиза (например, `release/1.0.0`)
- `hotfix/#<N>` - срочные исправления в production

### Установка инструментов

```bash
# Установка commitizen
pip install commitizen

# Или через uv (рекомендуется)
uv pip install commitizen

# Установка pre-commit
pip install pre-commit

# Или через uv (рекомендуется)
uv pip install pre-commit

# Установка git-flow (опционально)
# Ubuntu/Debian:
sudo apt-get install git-flow

# macOS:
brew install git-flow

# Инициализация git-flow (один раз для проекта)
git flow init -d

# Установка pre-commit hooks (один раз для проекта)
pre-commit install
```

### Правила

1. **Все коммиты** должны соответствовать Conventional Commits
2. **Обязательно указывайте номер задачи** в формате `#N`
3. **Feature branches** именуются как `feature/#N`
4. **Pull Request** только в `develop`
5. Код должен проходить **линтеры** (ruff, black, mypy) - автоматически проверяется через pre-commit hooks
6. Все **тесты** должны быть зелёными
7. Добавляйте **тесты** для новой функциональности
8. Обновляйте **документацию** при необходимости

### Проверка перед коммитом

Проект использует **pre-commit hooks** для автоматической проверки кода перед каждым коммитом. Это включает:

- **Форматирование кода** (ruff-format)
- **Линтинг и исправление** (ruff с автофиксами)
- **Проверка безопасности** (bandit, semgrep, detect-secrets)
- **Проверка уязвимых зависимостей** (safety - запускается отдельно)
- **Базовые проверки** (trailing-whitespace, end-of-file-fixer, etc.)

```bash
# Ручной запуск всех проверок
pre-commit run --all-files

# Или только на изменённых файлах (автоматически перед коммитом)
pre-commit run

# Проверка уязвимых зависимостей (safety запускается отдельно)
pip install safety
safety check
```

Если проверки не проходят, pre-commit автоматически исправит то, что можно исправить, и покажет ошибки для ручного исправления.

### Пример полного workflow

```bash
# 1. Создать issue на GitHub (например, #42)

# 2. Создать feature branch
git checkout develop
git pull origin develop
git flow feature start #42

# 3. Внести изменения
# ... пишем код ...

# 4. Коммитим с номером задачи
git add .
cz commit
# Вводим: feat(api): #42 - add user authentication

# 5. Пушим
git push origin feature/#42

# 6. Создаем Pull Request в develop
# Название PR: "[#42] Add user authentication"
```

### Версионирование

Проект использует [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): breaking changes
- **MINOR** (0.1.0): новая функциональность (backwards compatible)
- **PATCH** (0.0.1): bug fixes

Версии управляются через Commitizen:
```bash
# Автоматический bump версии на основе коммитов
cz bump

# Создание changelog
cz changelog
```

## 📄 Лицензия

**CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International)

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

### Вы можете:
- ✅ **Делиться** — копировать и распространять материал
- ✅ **Адаптировать** — изменять, преобразовывать и создавать на основе материала

### При условиях:
- 📝 **Атрибуция** — Вы должны указать авторство
- 🚫 **Некоммерческое использование** — Нельзя использовать в коммерческих целях без разрешения автора
- 🔄 **С сохранением условий** — При изменении, распространять под той же лицензией

### Коммерческое использование
Для использования проекта в коммерческих целях свяжитесь с автором для получения разрешения:
- Email: ogodevonline@gmail.com
- GitHub: [@VasiliySilver](https://github.com/VasiliySilver)

Полный текст лицензии: [LICENSE](LICENSE)


## 📞 Контакты

- Email: ogodevonline@gmail.com
- GitHub: [@VasiliySilver](https://github.com/VasiliySilver)

---
