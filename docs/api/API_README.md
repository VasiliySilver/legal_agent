# Legal Agent API

REST API для юридического агента по Трудовому Кодексу РФ.

## 🚀 Быстрый старт

### Установка зависимостей

```bash
# С использованием uv (рекомендуется)
uv sync

# Или с pip
pip install -e .
```

### Настройка переменных окружения

Создайте файл `.env`:

```env
# База данных
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legal_agent

# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Опционально: прокси для Groq API
GROQ_PROXY=socks5://127.0.0.1:12334/

# Эмбеддинги
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### Запуск базы данных

```bash
# Запуск PostgreSQL через Docker
cd docker
docker-compose up -d

# Инициализация БД
python -m src.infrastructure.database init
```

### Запуск API сервера

```bash
# Режим разработки (с автоперезагрузкой)
python -m src.api.main

# Или через uvicorn напрямую
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: `http://localhost:8000`

## 📚 Документация API

После запуска сервера доступны:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

## 🔌 API Endpoints

### Вопросы

#### POST `/api/v1/questions`
Задать юридический вопрос с сохранением истории.

**Request:**
```json
{
  "question": "Как уволиться по собственному желанию?",
  "user_id": "user123",
  "conversation_id": "conv456"  // опционально
}
```

**Response:**
```json
{
  "answer": "Работник имеет право расторгнуть трудовой договор...",
  "articles": [
    {
      "number": "80",
      "title": "Расторжение трудового договора по инициативе работника",
      "content": "..."
    }
  ],
  "metadata": {
    "confidence": 0.95,
    "sources_count": 1,
    "article_numbers": ["80"]
  },
  "conversation_id": "conv456"
}
```

#### POST `/api/v1/questions/quick`
Быстрый ответ без сохранения истории.

**Request:**
```json
{
  "question": "Сколько дней отпуска положено?"
}
```

### Диалоги

#### GET `/api/v1/conversations?user_id=user123`
Получить список диалогов пользователя.

#### POST `/api/v1/conversations`
Создать новый диалог.

#### GET `/api/v1/conversations/{conversation_id}`
Получить диалог с историей сообщений.

#### PATCH `/api/v1/conversations/{conversation_id}`
Обновить диалог (название).

#### DELETE `/api/v1/conversations/{conversation_id}`
Удалить диалог.

### Статьи ТК РФ

#### GET `/api/v1/articles?query=увольнение&strategy=semantic&limit=5`
Поиск статей.

Параметры:
- `query` - поисковый запрос
- `strategy` - стратегия поиска: `by_number`, `fulltext`, `semantic`
- `limit` - количество результатов (1-50)

#### GET `/api/v1/articles/{number}`
Получить статью по номеру.

#### POST `/api/v1/articles/search`
Поиск статей через POST (с телом запроса).

### Служебные

#### GET `/`
Главная страница API.

#### GET `/health`
Healthcheck (проверка работоспособности).

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск только API тестов
pytest tests/api/

# С покрытием кода
pytest --cov=src tests/

# Подробный вывод
pytest -v tests/api/
```

## 🏗️ Архитектура

Проект следует **Clean Architecture** (DDD):

```
src/
├── domain/          # Бизнес-логика (entities)
├── application/     # Use cases, сервисы
├── infrastructure/  # БД, репозитории
└── api/            # FastAPI endpoints
    ├── dependencies.py    # DI контейнер
    ├── schemas/          # Pydantic модели
    │   ├── requests.py
    │   └── responses.py
    ├── routes/           # API роуты
    │   ├── questions.py
    │   ├── conversations.py
    │   └── articles.py
    └── main.py           # FastAPI app
```

### Ключевые компоненты

#### Dependencies (DI)
Все зависимости (репозитории, сервисы, use cases) инжектятся через FastAPI Depends:

```python
from fastapi import Depends
from src.api.dependencies import get_quick_answer_use_case

@router.post("/questions/quick")
async def ask_quick(
    request: QuickQuestionRequest,
    use_case = Depends(get_quick_answer_use_case)
):
    ...
```

#### Schemas
Валидация запросов и форматирование ответов через Pydantic:

```python
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    user_id: str
```

#### Routes
Каждый модуль имеет свой APIRouter:

- `questions_router` - вопросы
- `conversations_router` - диалоги
- `articles_router` - статьи

## 🔐 Безопасность

### CORS
По умолчанию разрешены все источники (`allow_origins=["*"]`).

⚠️ **В production** укажите конкретные домены:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    ...
)
```

### Rate Limiting
TODO: Добавить rate limiting для защиты от злоупотреблений.

## 📊 Мониторинг

### Логирование
Все запросы логируются через middleware:

```
📨 POST /api/v1/questions
📤 POST /api/v1/questions - 200
```

### Health Check
Endpoint `/health` проверяет:
- Статус API
- Подключение к БД
- Timestamp

## 🚢 Production Deployment

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -e .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
GROQ_API_KEY=...
```

### Запуск

```bash
uvicorn src.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

## 🐛 Troubleshooting

### Ошибка подключения к БД
```
❌ Ошибка подключения к БД
```

**Решение:**
1. Проверьте, запущен ли PostgreSQL
2. Проверьте переменные окружения
3. Запустите `docker-compose up -d`

### Import errors
```
ImportError: cannot import name 'get_async_session'
```

**Решение:**
1. Установите все зависимости: `uv sync`
2. Убедитесь, что используете правильный Python (3.12+)

### GROQ_API_KEY not found
```
ValueError: GROQ_API_KEY не установлен
```

**Решение:**
1. Создайте `.env` файл
2. Добавьте `GROQ_API_KEY=your_key`

## 📝 TODO

- [ ] Добавить аутентификацию (JWT)
- [ ] Добавить rate limiting
- [ ] Добавить кеширование ответов
- [ ] Добавить metrics (Prometheus)
- [ ] Добавить WebSocket для streaming ответов
- [ ] Добавить пагинацию для списка диалогов
- [ ] Добавить фильтры для поиска статей

## 📄 Лицензия

MIT
