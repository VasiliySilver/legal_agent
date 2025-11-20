"""
Тесты для векторного сервиса.

Тестируем создание эмбеддингов и семантический поиск статей.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import numpy as np
import pytest

from src.domain.entities import Article
from src.application.services.vector_service import (
    VectorService,
    FAISSVectorStore,
    VectorBackend,
)


@pytest.fixture
def sample_articles():
    """Примеры статей для тестирования."""
    return [
        Article(
            id=uuid4(),
            number="80",
            title="Расторжение трудового договора по инициативе работника",
            content="Работник имеет право расторгнуть трудовой договор...",
            chapter="Глава 13. Прекращение трудового договора",
        ),
        Article(
            id=uuid4(),
            number="77",
            title="Отпуск без сохранения заработной платы",
            content="Работнику по семейным обстоятельствам...",
            chapter="Глава 19. Отпуска",
        ),
    ]


class TestVectorService:
    """Тесты для векторного поиска."""

    @pytest.mark.asyncio
    async def test_create_embeddings(self, sample_articles):
        """Тест: создание эмбеддингов для статей."""
        # Arrange
        with patch("src.application.services.vector_service.SentenceTransformer") as mock_model:
            # paraphrase-multilingual-MiniLM-L12-v2 создаёт 384-мерные эмбеддинги
            mock_embeddings = np.random.rand(2, 384).astype(np.float32)
            mock_model.return_value.encode = Mock(return_value=mock_embeddings)

            service = VectorService(backend=VectorBackend.FAISS)

            # Act
            embeddings = await service.create_embeddings(sample_articles)

            # Assert
            assert embeddings.shape == (2, 384)
            mock_model.return_value.encode.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_faiss_index(self, sample_articles):
        """Тест: построение FAISS индекса."""
        # Arrange
        embedding_dim = 384
        
        with patch("sentence_transformers.SentenceTransformer") as mock_model:
            mock_embeddings = np.random.rand(2, embedding_dim).astype(np.float32)
            mock_model.return_value.encode = Mock(return_value=mock_embeddings)

            with patch("faiss.IndexFlatL2") as mock_index_class:
                mock_index = Mock()
                mock_index.add = Mock()
                mock_index_class.return_value = mock_index

                service = VectorService(backend=VectorBackend.FAISS)

                # Act
                await service.build_index(sample_articles)

                # Assert
                mock_index_class.assert_called_once_with(embedding_dim)  # Размерность
                # Проверяем, что add был вызван с эмбеддингами правильной формы
                call_args = mock_index.add.call_args
                added_vectors = call_args[0][0]
                assert added_vectors.shape == (2, embedding_dim)
                assert service.articles == sample_articles

    @pytest.mark.asyncio
    async def test_find_similar_articles(self, sample_articles):
        """Тест: поиск похожих статей."""
        # Arrange
        query = "как расторгнуть трудовой договор"

        with patch("sentence_transformers.SentenceTransformer") as mock_model:
            # Эмбеддинги для статей при build_index
            mock_model.return_value.encode = Mock(
                side_effect=[
                    np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),  # build_index
                    np.array([[0.15, 0.25, 0.35]]),  # find_similar query
                ]
            )

            with patch("faiss.IndexFlatL2") as mock_index_class:
                mock_index = Mock()
                mock_index.add = Mock()
                # Поиск возвращает расстояния и индексы
                mock_index.search = Mock(
                    return_value=(
                        np.array([[0.05, 0.5]]),  # Расстояния
                        np.array([[0, 1]]),  # Индексы
                    )
                )
                mock_index_class.return_value = mock_index

                service = VectorService(backend=VectorBackend.FAISS)

                # Act
                await service.build_index(sample_articles)
                results = await service.find_similar(query, top_k=2)

                # Assert
                assert len(results) == 2
                assert results[0] == sample_articles[0]  # Самый похожий
                assert results[1] == sample_articles[1]
                mock_index.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_similar_with_threshold(self, sample_articles):
        """Тест: поиск с порогом похожести."""
        # Arrange
        query = "отпуск"
        threshold = 0.3

        with patch("sentence_transformers.SentenceTransformer") as mock_model:
            mock_model.return_value.encode = Mock(
                side_effect=[
                    np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
                    np.array([[0.15, 0.25, 0.35]]),
                ]
            )

            with patch("faiss.IndexFlatL2") as mock_index_class:
                mock_index = Mock()
                mock_index.add = Mock()
                # Второй результат слишком далёк
                mock_index.search = Mock(
                    return_value=(
                        np.array([[0.05, 0.8]]),  # Расстояния
                        np.array([[0, 1]]),  # Индексы
                    )
                )
                mock_index_class.return_value = mock_index

                service = VectorService(backend=VectorBackend.FAISS)

                # Act
                await service.build_index(sample_articles)
                results = await service.find_similar(
                    query, top_k=2, threshold=threshold
                )

                # Assert
                # Только первый прошёл порог (0.05 < 0.3)
                assert len(results) == 1
                assert results[0] == sample_articles[0]

    @pytest.mark.asyncio
    async def test_save_and_load_index(self, tmp_path, sample_articles):
        """Тест: сохранение и загрузка индекса."""
        # Arrange
        index_path = str(tmp_path / "test_index")
        embedding_dim = 384

        with patch("src.application.services.vector_service.SentenceTransformer") as mock_model:
            mock_embeddings = np.random.rand(2, embedding_dim).astype(np.float32)
            mock_model.return_value.encode = Mock(return_value=mock_embeddings)

            # Не мокируем faiss - пусть файлы реально создаются
            service = VectorService(backend=VectorBackend.FAISS)

            # Act
            await service.build_index(sample_articles)
            await service.save_index(index_path)

            service2 = VectorService(backend=VectorBackend.FAISS)
            await service2.load_index(index_path, sample_articles)

            # Assert
            assert service2.articles == sample_articles
            assert (tmp_path / "test_index.faiss").exists()
            assert (tmp_path / "test_index.articles.pkl").exists()
            assert (tmp_path / "test_index.meta.pkl").exists()

    @pytest.mark.asyncio
    async def test_empty_query(self, sample_articles):
        """Тест: пустой поисковый запрос."""
        # Arrange
        query = ""

        with patch("sentence_transformers.SentenceTransformer") as mock_model:
            mock_model.return_value.encode = Mock(
                return_value=np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
            )

            with patch("faiss.IndexFlatL2") as mock_index_class:
                mock_index = Mock()
                mock_index_class.return_value = mock_index

                service = VectorService(backend=VectorBackend.FAISS)
                await service.build_index(sample_articles)

                # Act & Assert
                with pytest.raises(ValueError, match="cannot be empty"):
                    await service.find_similar(query)

    @pytest.mark.asyncio
    async def test_search_without_index(self):
        """Тест: поиск без построенного индекса."""
        # Arrange
        query = "test"
        service = VectorService(backend=VectorBackend.FAISS)

        # Act & Assert
        with pytest.raises(ValueError, match="Index not built"):
            await service.find_similar(query)

    @pytest.mark.asyncio
    async def test_vector_backend_selection(self):
        """Тест: выбор бэкенда векторного поиска."""
        # FAISS
        service_faiss = VectorService(backend=VectorBackend.FAISS)
        assert isinstance(service_faiss.store, FAISSVectorStore)

        # PostgreSQL (требует подключение к БД, поэтому просто проверяем создание)
        # Для полноценного теста PostgresVectorStore нужна реальная БД
        # service_postgres = VectorService(backend=VectorBackend.POSTGRES, db_url="...")

    @pytest.mark.asyncio
    async def test_create_embeddings_empty_list(self, sample_articles):
        """Тест: создание эмбеддингов для пустого списка."""
        # Arrange
        service = VectorService(backend=VectorBackend.FAISS)

        # Act & Assert
        embeddings = await service.create_embeddings([])
        assert embeddings.shape[0] == 0

    @pytest.mark.asyncio
    async def test_find_similar_top_k_limit(self, sample_articles):
        """Тест: ограничение количества результатов."""
        # Arrange
        query = "test"
        top_k = 1

        with patch("sentence_transformers.SentenceTransformer") as mock_model:
            mock_model.return_value.encode = Mock(
                side_effect=[
                    np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),
                    np.array([[0.15, 0.25, 0.35]]),
                ]
            )

            with patch("faiss.IndexFlatL2") as mock_index_class:
                mock_index = Mock()
                mock_index.add = Mock()
                mock_index.search = Mock(
                    return_value=(
                        np.array([[0.05]]),  # Только 1 результат
                        np.array([[0]]),
                    )
                )
                mock_index_class.return_value = mock_index

                service = VectorService(backend=VectorBackend.FAISS)

                # Act
                await service.build_index(sample_articles)
                results = await service.find_similar(query, top_k=top_k)

                # Assert
                assert len(results) == 1
                # Проверяем, что search был вызван с правильным top_k
                call_args = mock_index.search.call_args
                assert call_args[0][1] == top_k  # Второй аргумент - top_k


class TestFAISSVectorStore:
    """Тесты для FAISS хранилища."""

    @pytest.mark.asyncio
    async def test_add_vectors(self):
        """Тест: добавление векторов в FAISS."""
        # Arrange
        vectors = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        articles = []  # Пустой список для теста

        with patch("faiss.IndexFlatL2") as mock_index_class:
            mock_index = Mock()
            mock_index.add = Mock()
            mock_index_class.return_value = mock_index

            store = FAISSVectorStore()

            # Act
            await store.add_vectors(vectors, articles)

            # Assert
            mock_index_class.assert_called_once_with(3)  # Размерность
            mock_index.add.assert_called_once()
            assert store.dimension == 3

    @pytest.mark.asyncio
    async def test_add_empty_vectors(self):
        """Тест: добавление пустого массива векторов."""
        # Arrange
        vectors = np.array([])
        articles = []

        store = FAISSVectorStore()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot add empty vectors"):
            await store.add_vectors(vectors, articles)

    @pytest.mark.asyncio
    async def test_search(self):
        """Тест: поиск в FAISS индексе."""
        # Arrange
        query_vector = np.array([[0.15, 0.25, 0.35]])

        with patch("faiss.IndexFlatL2") as mock_index_class:
            mock_index = Mock()
            mock_index.search = Mock(
                return_value=(
                    np.array([[0.1, 0.5]]),
                    np.array([[0, 1]]),
                )
            )
            mock_index_class.return_value = mock_index

            store = FAISSVectorStore()
            store.index = mock_index

            # Act
            distances, indices = await store.search(query_vector, top_k=2)

            # Assert
            mock_index.search.assert_called_once()
            assert len(distances) == 2
            assert len(indices) == 2


class TestVectorServiceIntegration:
    """Интеграционные тесты векторного сервиса."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, sample_articles):
        """Тест: полный цикл работы с векторным поиском."""
        # Arrange
        with patch("sentence_transformers.SentenceTransformer") as mock_model:
            mock_model.return_value.encode = Mock(
                side_effect=[
                    np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]),  # build
                    np.array([[0.11, 0.21, 0.31]]),  # search 1
                    np.array([[0.4, 0.5, 0.6]]),  # search 2
                ]
            )

            with patch("faiss.IndexFlatL2") as mock_index_class:
                mock_index = Mock()
                mock_index.add = Mock()

                # Первый поиск - находим статью 80
                # Второй поиск - находим статью 77
                mock_index.search = Mock(
                    side_effect=[
                        (np.array([[0.01]]), np.array([[0]])),
                        (np.array([[0.01]]), np.array([[1]])),
                    ]
                )
                mock_index_class.return_value = mock_index

                service = VectorService(backend=VectorBackend.FAISS)

                # Act
                # 1. Создание индекса
                await service.build_index(sample_articles)

                # 2. Первый поиск
                results1 = await service.find_similar(
                    "расторжение договора", top_k=1
                )

                # 3. Второй поиск
                results2 = await service.find_similar("отпуск", top_k=1)

                # Assert
                assert len(results1) == 1
                assert results1[0].number == "80"

                assert len(results2) == 1
                assert results2[0].number == "77"
