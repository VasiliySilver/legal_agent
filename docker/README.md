# Docker инфраструктура для Legal Agent

## 📦 Что включено

- **PostgreSQL 16** (Alpine) — легковесный образ
- **Персистентное хранилище** — данные сохраняются при перезапуске
- **Healthcheck** — автоматическая проверка здоровья БД
- **Инициализация** — автоматическая настройка расширений (pg_trgm, uuid-ossp)
- **Русская локаль** — корректный полнотекстовый поиск по русскому языку

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
# Подключиться к БД через psql
docker compose exec postgres psql -U postgres -d legal_agent

# Или через любой GUI клиент:
# Host: localhost
# Port: 5432
# User: postgres
# Password: (из .env файла)
# Database: legal_agent
```

## 📋 Полезные команды

```bash
# Остановка
docker compose down

# Остановка + удаление volumes (⚠️ удалит все данные!)
docker compose down -v

# Перезапуск
docker compose restart

# Логи
docker compose logs postgres

# Выполнить SQL запрос
docker compose exec postgres psql -U postgres -d legal_agent -c "SELECT version();"

# Бэкап БД
docker compose exec postgres pg_dump -U postgres legal_agent > backup.sql

# Восстановление БД
cat backup.sql | docker compose exec -T postgres psql -U postgres -d legal_agent
```

## 🔧 Настройка приложения

После запуска Docker Compose, настрой подключение в приложении:

### Создай `.env` в корне проекта:

```env
# PostgreSQL (Docker)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legal_agent

# Или используй DATABASE_URL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/legal_agent
```

### Проверь подключение:

```bash
# Из корня проекта
python -m src.infrastructure.database check
```

## 📊 Мониторинг

```bash
# Статус контейнера
docker compose ps

# Использование ресурсов
docker stats legal_agent_postgres

# Healthcheck
docker inspect legal_agent_postgres | grep -A 10 Health
```

## 🛑 Очистка

```bash
# Остановить и удалить всё
docker compose down -v

# Удалить образы
docker rmi postgres:16-alpine
```

## 💡 Production советы

1. **Измени пароль** в `.env` на надёжный
2. **Настрой backups** (pg_dump в cron)
3. **Используй Docker secrets** вместо .env
4. **Настрой лимиты ресурсов** (раскомментируй deploy в docker-compose.yml)
5. **Используй внешний volume** для важных данных
