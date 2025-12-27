# Legal Agent Telegram Bot

Telegram бот для юридических консультаций по Трудовому Кодексу РФ.

## 🚀 Быстрый старт

### 1. Создай бота через @BotFather

1. Открой [@BotFather](https://t.me/botfather) в Telegram
2. Отправь `/newbot`
3. Следуй инструкциям
4. Получи токен вида: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Настрой окружение

Создай файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Добавь в `.env`:

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather

# API
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30.0

# Logging
LOG_LEVEL=INFO
```

### 3. Запуск

```bash
# Отключить IPv6 (важно для стабильной работы!)
make disable-ipv6

# Запуск бота
make run-bot

# Или напрямую
python run_bot.py
```

### 4. Использование

- Найди бота в Telegram: @legal_agent_rf_bot
- Отправь `/start` для начала
- Задавай вопросы по Трудовому Кодексу РФ

## 🛠️ Команды

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- Любой текст - вопрос по ТК РФ

## ⚙️ Настройка

### Переменные окружения

- `BOT_TOKEN` - Токен от @BotFather
- `API_BASE_URL` - URL REST API (по умолчанию http://localhost:8000)
- `LOG_LEVEL` - Уровень логирования (DEBUG, INFO, WARNING, ERROR)
- `RATE_LIMIT_PER_USER` - Ограничение запросов в минуту (по умолчанию 10)

### Rate Limiting

Бот имеет встроенную защиту от спама:
- 10 сообщений в минуту на пользователя
- Автоматическое логирование всех действий

## 🐛 Troubleshooting

**Бот не подключается к Telegram?**
```bash
# Отключи IPv6
make disable-ipv6

# Проверь токен
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

**API недоступен?**
```bash
# Проверь, запущен ли API
curl http://localhost:8000/health
```

**Ошибки подключения к БД?**
```bash
# Проверь Docker
docker ps | grep postgres
```
