"""
Сервис для векторного поиска статей ТК РФ.

Поддерживает разные бэкенды:
- FAISS (локальный, быстрый)
- PostgreSQL с pgvector (production, персистентный)
"""

import pickle
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from src.domain.entities import Article


class VectorBackend(str, Enum):
    """Типы бэкендов для векторного поиска."""

    FAISS = "faiss"
    POSTGRES = "postgres"


# ============================================================================
# Абстрактный базовый класс для векторных хранилищ
# ============================================================================


class VectorStore(ABC):
    """Абстрактное хранилище для векторного поиска."""

    @abstractmethod
    async def add_vectors(self, vectors: np.ndarray, articles: list[Article]) -> None:
        """Добавить векторы в хранилище."""
        pass

    @abstractmethod
    async def search(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> tuple[list[float], list[int]]:
        """
        Поиск похожих векторов.

        Returns:
            (distances, indices) - расстояния и индексы найденных векторов
        """
        pass

    @abstractmethod
    async def save(self, path: str) -> None:
        """Сохранить хранилище."""
        pass

    @abstractmethod
    async def load(self, path: str) -> None:
        """Загрузить хранилище."""
        pass


# ============================================================================
# FAISS бэкенд (локальный, in-memory)
# ============================================================================


class FAISSVectorStore(VectorStore):
    """Векторное хранилище на основе FAISS."""

    def __init__(self):
        """Инициализация FAISS хранилища."""
        try:
            import faiss

            self.faiss = faiss
        except ImportError:
            raise ImportError(
                "FAISS not installed. Install it with: pip install faiss-cpu"
            )

        self.index: Optional[any] = None
        self.dimension: Optional[int] = None

    async def add_vectors(self, vectors: np.ndarray, articles: list[Article]) -> None:
        """Добавить векторы в FAISS индекс."""
        if vectors.shape[0] == 0:
            raise ValueError("Cannot add empty vectors")

        self.dimension = vectors.shape[1]
        self.index = self.faiss.IndexFlatL2(self.dimension)
        self.index.add(vectors.astype(np.float32))

    async def search(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> tuple[list[float], list[int]]:
        """Поиск в FAISS индексе."""
        if self.index is None:
            raise ValueError("Index not initialized")

        distances, indices = self.index.search(query_vector.astype(np.float32), top_k)
        return distances[0].tolist(), indices[0].tolist()

    async def save(self, path: str) -> None:
        """Сохранить FAISS индекс."""
        if self.index is None:
            raise ValueError("Index not initialized")

        self.faiss.write_index(self.index, path)

    async def load(self, path: str) -> None:
        """Загрузить FAISS индекс."""
        self.index = self.faiss.read_index(path)


# ============================================================================
# PostgreSQL + pgvector бэкенд
# ============================================================================


class PostgresVectorStore(VectorStore):
    """Векторное хранилище на основе PostgreSQL с pgvector."""

    def __init__(self, connection_string: str, table_name: str = "article_vectors"):
        """
        Инициализация PostgreSQL хранилища.

        Args:
            connection_string: Строка подключения к БД
            table_name: Название таблицы для векторов
        """
        try:
            import asyncpg

            self.asyncpg = asyncpg
        except ImportError:
            raise ImportError(
                "asyncpg not installed. Install it with: pip install asyncpg"
            )

        self.connection_string = connection_string
        self.table_name = table_name
        self.pool: Optional[any] = None

    async def _init_pool(self) -> None:
        """Инициализация пула соединений."""
        if self.pool is None:
            self.pool = await self.asyncpg.create_pool(self.connection_string)

    async def _ensure_pgvector(self) -> None:
        """Проверка и создание расширения pgvector."""
        await self._init_pool()
        async with self.pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    async def _create_table(self, dimension: int) -> None:
        """
        Создание таблицы для векторов.

        Args:
            dimension: Размерность векторов
        """
        await self._ensure_pgvector()
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    article_id UUID NOT NULL,
                    embedding vector({dimension}) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                ON {self.table_name} USING ivfflat (embedding vector_l2_ops)
                WITH (lists = 100);
            """)

    async def add_vectors(self, vectors: np.ndarray, articles: list[Article]) -> None:
        """Добавить векторы в PostgreSQL."""
        if vectors.shape[0] == 0:
            raise ValueError("Cannot add empty vectors")

        if vectors.shape[0] != len(articles):
            raise ValueError("Number of vectors must match number of articles")

        dimension = vectors.shape[1]
        await self._create_table(dimension)

        # Удаляем старые векторы и выполняем пакетную вставку для скорости
        async with self.pool.acquire() as conn:
            await conn.execute(f"TRUNCATE TABLE {self.table_name};")

            # Подготавливаем параметры для пакетной вставки
            params = []
            for article, vector in zip(articles, vectors):
                vec_list = vector.tolist()
                vec_str = "[" + ",".join(str(float(x)) for x in vec_list) + "]"
                params.append((str(article.id), vec_str))

            if params:
                stmt = f"INSERT INTO {self.table_name} (article_id, embedding) VALUES ($1::uuid, $2::vector)"
                await conn.executemany(stmt, params)

    async def search(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> tuple[list[float], list[int]]:
        """Поиск в PostgreSQL с использованием vector."""
        await self._init_pool()

        async with self.pool.acquire() as conn:
            # Ensure we pass a single vector string (pgvector expects e.g. "[0.1,0.2,...]")
            # `query_vector` may be a 2D array (1, dim) from the encoder, so extract the row.
            q = query_vector
            try:
                import numpy as _np

                q = _np.asarray(query_vector)
                if q.ndim > 1 and q.shape[0] == 1:
                    q = q[0]
            except Exception:
                # fallback: use as-is
                q = query_vector

            if hasattr(q, "tolist"):
                q_list = q.tolist()
            else:
                q_list = list(q)

            q_str = "[" + ",".join(str(float(x)) for x in q_list) + "]"

            rows = await conn.fetch(
                f"""
                SELECT
                    article_id,
                    embedding <-> $1::vector AS distance
                FROM {self.table_name}
                ORDER BY distance
                LIMIT $2
                """,
                q_str,
                top_k,
            )

        distances = [row["distance"] for row in rows]
        # Return article_id values (UUID strings) so caller can map to articles
        article_ids = [str(row["article_id"]) for row in rows]

        return distances, article_ids

    async def save(self, path: str) -> None:
        """PostgreSQL хранит данные персистентно, метод не нужен."""
        pass

    async def load(self, path: str) -> None:
        """PostgreSQL хранит данные персистентно, метод не нужен."""
        pass

    async def close(self) -> None:
        """Закрыть пул соединений."""
        if self.pool:
            await self.pool.close()


# ============================================================================
# Главный сервис векторного поиска
# ============================================================================


class VectorService:
    """Сервис для семантического поиска статей с помощью векторных эмбеддингов."""

    def __init__(
        self,
        backend: VectorBackend = VectorBackend.FAISS,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        connection_string: Optional[str] = None,
    ):
        """
        Инициализация векторного сервиса.

        Args:
            backend: Тип бэкенда (FAISS или PostgreSQL)
            model_name: Название модели для создания эмбеддингов
            connection_string: Строка подключения для PostgreSQL (если используется)
        """
        self.backend_type = backend
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.articles: list[Article] = []
        self.dimension: Optional[int] = None

        # Инициализация хранилища в зависимости от бэкенда
        if backend == VectorBackend.FAISS:
            self.store = FAISSVectorStore()
        elif backend == VectorBackend.POSTGRES:
            if not connection_string:
                raise ValueError("connection_string required for PostgreSQL backend")
            self.store = PostgresVectorStore(connection_string)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def _load_model(self) -> SentenceTransformer:
        """
        Загрузка модели для создания эмбеддингов (ленивая загрузка).

        Returns:
            Загруженная модель
        """
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model

    async def create_embeddings(self, articles: list[Article]) -> np.ndarray:
        """
        Создание эмбеддингов для статей.

        Args:
            articles: Список статей для эмбеддинга

        Returns:
            Массив эмбеддингов (numpy array)
        """
        if not articles:
            return np.array([])

        model = self._load_model()

        # Создаём текст для эмбеддинга из заголовка и содержимого
        texts = [f"{article.title}. {article.content}" for article in articles]

        # Генерируем эмбеддинги
        embeddings = model.encode(texts, show_progress_bar=True)

        return embeddings

    async def build_index(self, articles: list[Article]) -> None:
        """
        Построение индекса для статей.

        Args:
            articles: Список статей для индексации

        Raises:
            ValueError: Если список статей пустой
        """
        if not articles:
            raise ValueError("Cannot build index from empty articles list")

        # Создаём эмбеддинги
        embeddings = await self.create_embeddings(articles)

        # Сохраняем размерность
        self.dimension = embeddings.shape[1]

        # Добавляем в хранилище
        await self.store.add_vectors(embeddings, articles)

        # Сохраняем ссылку на статьи
        self.articles = articles

        print(
            f"✓ Built {self.backend_type} index with {len(articles)} articles, dimension={self.dimension}"
        )

    async def find_similar(
        self,
        query: str,
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> list[Article]:
        """
        Поиск похожих статей по запросу.

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            threshold: Порог расстояния (статьи дальше будут отфильтрованы)

        Returns:
            Список наиболее похожих статей

        Raises:
            ValueError: Если индекс не построен или запрос пустой
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not self.articles:
            raise ValueError("Index not built. Call build_index() first.")

        # Создаём эмбеддинг для запроса
        model = self._load_model()
        query_embedding = model.encode([query])

        # Ищем в хранилище
        distances, indices = await self.store.search(query_embedding, top_k)

        # Формируем результаты
        results = []

        # Если backend POSTGRES returns article_id strings, map them to articles
        if indices and isinstance(indices[0], str):
            id_map = {str(a.id): a for a in self.articles}

            for aid, distance in zip(indices, distances):
                if threshold is not None and distance > threshold:
                    continue

                article = id_map.get(aid)
                if article is not None:
                    results.append(article)

            return results

        # Otherwise assume numeric indices (FAISS)
        for idx, distance in zip(indices, distances):
            if threshold is not None and distance > threshold:
                continue

            if 0 <= idx < len(self.articles):
                results.append(self.articles[idx])

        return results

    async def save_index(self, path: str) -> None:
        """
        Сохранение индекса на диск.

        Args:
            path: Путь для сохранения (без расширения)

        Raises:
            ValueError: Если индекс не построен
        """
        if not self.articles:
            raise ValueError("Index not built. Nothing to save.")

        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем хранилище
        if self.backend_type == VectorBackend.FAISS:
            await self.store.save(f"{path}.faiss")

        # Сохраняем статьи
        with open(f"{path}.articles.pkl", "wb") as f:
            pickle.dump(self.articles, f)

        # Сохраняем метаданные
        metadata = {
            "backend": self.backend_type,
            "model_name": self.model_name,
            "dimension": self.dimension,
            "num_articles": len(self.articles),
        }
        with open(f"{path}.meta.pkl", "wb") as f:
            pickle.dump(metadata, f)

        print(f"✓ Saved {self.backend_type} index to {path}")

    async def load_index(
        self, path: str, articles: Optional[list[Article]] = None
    ) -> None:
        """
        Загрузка индекса с диска.

        Args:
            path: Путь к сохранённому индексу (без расширения)
            articles: Список статей (если None, загружается из pickle)

        Raises:
            FileNotFoundError: Если файлы индекса не найдены
        """
        # Загружаем хранилище
        if self.backend_type == VectorBackend.FAISS:
            faiss_path = f"{path}.faiss"
            if not Path(faiss_path).exists():
                raise FileNotFoundError(f"Index not found: {faiss_path}")
            await self.store.load(faiss_path)

        # Загружаем статьи
        if articles is not None:
            self.articles = articles
        else:
            articles_path = f"{path}.articles.pkl"
            if not Path(articles_path).exists():
                raise FileNotFoundError(f"Articles file not found: {articles_path}")

            with open(articles_path, "rb") as f:
                self.articles = pickle.load(f)

        # Загружаем метаданные
        meta_path = f"{path}.meta.pkl"
        if Path(meta_path).exists():
            with open(meta_path, "rb") as f:
                metadata = pickle.load(f)
                self.dimension = metadata.get("dimension")

        print(
            f"✓ Loaded {self.backend_type} index from {path} ({len(self.articles)} articles)"
        )

    def get_stats(self) -> dict[str, any]:
        """
        Получение статистики индекса.

        Returns:
            Словарь со статистикой
        """
        return {
            "backend": self.backend_type,
            "model_name": self.model_name,
            "dimension": self.dimension,
            "num_articles": len(self.articles),
            "index_built": len(self.articles) > 0,
        }

    async def close(self) -> None:
        """Закрытие соединений (для PostgreSQL)."""
        if isinstance(self.store, PostgresVectorStore):
            await self.store.close()
