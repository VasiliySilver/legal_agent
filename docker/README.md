# Docker инфраструктура для Legal Agent

# Docker инфраструктура для Legal Agent

## 📦 Что включено

### Основная БД (postgres)
- **PostgreSQL 16** (Alpine) — легковесный образ
- **Порт**: 5432
- **Назначение**: статьи ТК РФ, диалоги, пользователи
- **Расширения**: pg_trgm (полнотекстовый поиск), uuid-ossp

### Векторная БД (postgres_vector)
- **PostgreSQL 16 + pgvector** — для эмбеддингов
- **Порт**: 5433
- **Назначение**: векторные эмбеддинги статей для семантического поиска
- **Расширения**: vector (pgvector), uuid-ossp

### Общее
- **Персистентное хранилище** — данные сохраняются при перезапуске
- **Healthcheck** — автоматическая проверка здоровья БД
- **Русская локаль** — корректный поиск по русскому языку

## 🚀 Быстрый старт

### 1. Настройка переменных окружения

```bash
# Скопируй example файл
cp .env.example .env

# Отредактируй .env (измени пароль!)
nano .env
```

### 2. Запуск

```bash
# Запуск в фоновом режиме
docker compose up -d

# Проверка статуса
docker compose ps

# Логи
docker compose logs -f postgres
```

### 3. Проверка подключения

```bash
# Основная БД
docker compose exec postgres psql -U postgres -d legal_agent

# Векторная БД
docker compose exec postgres_vector psql -U postgres -d legal_agent_vectors

# Проверить расширения в векторной БД
docker compose exec postgres_vector psql -U postgres -d legal_agent_vectors -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# Или через GUI клиенты:
# Основная БД: localhost:5432
# Векторная БД: localhost:5433
```

## 📋 Полезные команды

```bash
# Остановка обеих БД
docker compose down

# Остановка + удаление volumes (⚠️ удалит все данные!)
docker compose down -v

# Перезапуск
docker compose restart

# Логи основной БД
docker compose logs postgres

# Логи векторной БД
docker compose logs postgres_vector

# Обе БД
docker compose logs

# Выполнить SQL запрос (основная БД)
docker compose exec postgres psql -U postgres -d legal_agent -c "SELECT version();"

# Выполнить SQL запрос (векторная БД)
docker compose exec postgres_vector psql -U postgres -d legal_agent_vectors -c "SELECT version();"

# Бэкап основной БД
docker compose exec postgres pg_dump -U postgres legal_agent > backup_main.sql

# Бэкап векторной БД
docker compose exec postgres_vector pg_dump -U postgres legal_agent_vectors > backup_vectors.sql

# Восстановление основной БД
cat backup_main.sql | docker compose exec -T postgres psql -U postgres -d legal_agent

# Восстановление векторной БД
cat backup_vectors.sql | docker compose exec -T postgres_vector psql -U postgres -d legal_agent_vectors
```

## 🔧 Настройка приложения

После запуска Docker Compose, настрой подключение в приложении:

### Создай `.env` в корне проекта:

```env
# Основная PostgreSQL БД (статьи, диалоги)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legal_agent
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/legal_agent

# Векторная PostgreSQL БД (эмбеддинги)
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=postgres
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5433
VECTOR_DB_NAME=legal_agent_vectors
VECTOR_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/legal_agent_vectors
```

### Проверь подключение:

```bash
# Проверка основной БД
python -m src.infrastructure.database check

# В коде используй VectorService с PostgreSQL бэкендом
from src.application.services.vector_service import VectorService, VectorBackend

# FAISS (in-memory, для разработки)
vector_service = VectorService(backend=VectorBackend.FAISS)

# PostgreSQL (персистентный, для production)
vector_service = VectorService(
    backend=VectorBackend.POSTGRES,
    connection_string="postgresql://postgres:postgres@localhost:5433/legal_agent_vectors"
)
```

## 📊 Мониторинг

```bash
# Статус обоих контейнеров
docker compose ps

# Использование ресурсов основной БД
docker stats legal_agent_postgres

# Использование ресурсов векторной БД
docker stats legal_agent_postgres_vector

# Healthcheck основной БД
docker inspect legal_agent_postgres | grep -A 10 Health

# Healthcheck векторной БД
docker inspect legal_agent_postgres_vector | grep -A 10 Health
```

## 🛑 Очистка

```bash
# Остановить и удалить всё (включая volumes)
docker compose down -v

# Удалить образы
docker rmi postgres:16-alpine pgvector/pgvector:pg16
```

## 🏗️ Архитектура

### Зачем две БД?

**Основная БД (legal_agent)**
- Хранит структурированные данные
- CRUD операции, транзакции
- Полнотекстовый поиск (pg_trgm)
- Быстрые JOIN'ы и индексы

**Векторная БД (legal_agent_vectors)**
- Только эмбеддинги статей
- Оптимизирована для векторного поиска
- Независимое масштабирование
- Можно заменить на специализированные решения (Qdrant, Weaviate)

### Преимущества разделения:
✓ Изоляция нагрузки (поиск не влияет на основные операции)
✓ Разные настройки производительности
✓ Легче backup/restore
✓ Простая миграция на другие векторные БД

## 💡 Production советы

1. **Измени пароль** в `.env` на надёжный
2. **Настрой backups** (pg_dump в cron)
3. **Используй Docker secrets** вместо .env
4. **Настрой лимиты ресурсов** (раскомментируй deploy в docker-compose.yml)
5. **Используй внешний volume** для важных данных
