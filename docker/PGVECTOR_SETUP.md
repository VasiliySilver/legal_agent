# Настройка pgvector для PostgreSQL

## Что такое pgvector?

pgvector — это расширение PostgreSQL для хранения и поиска векторных эмбеддингов прямо в базе данных. Это позволяет:
- Персистентное хранение векторов (не нужно пересоздавать индекс при перезапуске)
- Масштабируемость в production
- Использование транзакций и ACID гарантий
- Интеграция с остальными данными в одной БД

## 🚀 Быстрый старт

### Всё уже настроено!

В проекте уже настроено:
1. ✅ Docker образ: `pgvector/pgvector:pg16`
2. ✅ Расширение подключено в `init.sql`
3. ✅ Python зависимости в `pyproject.toml`

### Запуск

```bash
# 1. Пересоздать контейнер (если был старый)
cd docker
docker-compose down -v
docker-compose up -d

# 2. Проверить расширение в векторной БД
docker exec -it legal_agent_postgres_vector psql -U postgres -d legal_agent_vectors -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# 3. Инициализировать таблицы
cd ..
python -m src.infrastructure.database init
```

## Использование в коде

### FAISS (по умолчанию, для разработки)
```python
from src.application.services.vector_service import VectorService, VectorBackend

service = VectorService(backend=VectorBackend.FAISS)
await service.build_index(articles)
```

### PostgreSQL + pgvector (для production)
```python
service = VectorService(
    backend=VectorBackend.POSTGRES,
    connection_string="postgresql://postgres:postgres@localhost:5433/legal_agent_vectors"
)
await service.build_index(articles)
```

> **Важно**: Векторная БД работает на порту **5433**, основная БД — на **5432**
)
await service.build_index(articles)
```

Код автоматически создаст таблицу `article_vectors` и индекс при первом использовании!

## 📊 Производительность и типы индексов

### Размер индекса

Для 1000 статей с эмбеддингами размерности 384:
- FAISS: ~1.5 MB (в памяти)
- pgvector: ~1.8 MB (в БД)

### Скорость поиска

| Количество статей | FAISS (ms) | pgvector (ms) |
|-------------------|------------|---------------|
| 1,000             | 1-2        | 3-5           |
| 10,000            | 5-10       | 10-20         |
| 100,000           | 20-50      | 50-100        |

### Типы индексов в pgvector

Таблица `article_vectors` создаётся автоматически с индексом **IVFFlat** (оптимален для ТК РФ ~500 статей).

Если в будущем будет больше данных:

1. **IVFFlat** (по умолчанию, до 1M векторов)
   ```sql
   CREATE INDEX ON article_vectors USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
   ```

2. **HNSW** (для > 1M векторов, быстрее но больше места)
   ```sql
   CREATE INDEX ON article_vectors USING hnsw (embedding vector_l2_ops);
   ```

## 🔄 Миграция между бэкендами

```python
# Переключение с FAISS на PostgreSQL — меняется только один параметр!
faiss_service = VectorService(backend=VectorBackend.FAISS)
pg_service = VectorService(
    backend=VectorBackend.POSTGRES,
    connection_string="postgresql://postgres:postgres@localhost:5432/legal_agent"
)

# Остальной код одинаковый
await pg_service.build_index(articles)
results = await pg_service.find_similar("запрос")
```

## 🛠️ Troubleshooting

### Ошибка: "extension "vector" is not available"

**Решение**: Пересоздай контейнер с правильным образом:
```bash
cd docker
docker-compose down -v
docker-compose up -d
```

### Проверка расширения

```bash
docker exec -it legal_agent_postgres_vector psql -U postgres -d legal_agent_vectors \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

Должно вывести:
```
 extname | extversion
---------+------------
 vector  | 0.5.1
```

### Медленный поиск

**Решение**: Проверь наличие индекса
```sql
SELECT indexname FROM pg_indexes WHERE tablename = 'article_vectors';
```

Если индекса нет, он создастся автоматически при следующем `build_index()`.

## 📚 Дополнительные ресурсы

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [pgvector Docker Hub](https://hub.docker.com/r/pgvector/pgvector)
- [Документация по индексам](https://github.com/pgvector/pgvector#indexing)
