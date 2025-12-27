# 🚀 Быстрый запуск API

## 1. Установка зависимостей

```bash
uv sync
```

## 2. Настройка окружения

Создайте `.env`:

```env
GROQ_API_KEY=your_api_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legal_agent
BOT_TOKEN=your_telegram_bot_token_here
```

## 3. Запуск БД

```bash
cd docker
docker-compose up -d
cd ..
python -m src.infrastructure.database init
```

## 4. Запуск API

```bash
# Простой способ
python run_api.py

# Или напрямую через uvicorn
uvicorn src.api.main:app --reload
```

API доступно на: http://localhost:8000
Документация: http://localhost:8000/docs

## 5. Запуск Telegram бота (опционально)

```bash
# Отключить IPv6 (важно!)
make disable-ipv6

# Запуск бота
make run-bot
```

Бот будет доступен в Telegram по username @legal_agent_rf_bot

## 5. Тестирование

```bash
# Все тесты
pytest

# Только API тесты
pytest tests/api/

# С подробным выводом
pytest -v tests/api/
```

## Примеры запросов

### Быстрый вопрос

```bash
curl -X POST http://localhost:8000/api/v1/questions/quick \
  -H "Content-Type: application/json" \
  -d '{"question": "Как уволиться по собственному желанию?"}'
```

### Вопрос с историей

```bash
curl -X POST http://localhost:8000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Как уволиться?",
    "user_id": "user123"
  }'
```

### Поиск статей

```bash
curl "http://localhost:8000/api/v1/articles?query=увольнение&strategy=semantic&limit=5"
```

## Troubleshooting

**БД не подключается?**
```bash
docker ps  # Проверить, запущен ли PostgreSQL
docker-compose logs postgres  # Посмотреть логи
```

**Import errors?**
```bash
uv sync  # Переустановить зависимости
```

Подробности в `API_README.md`
