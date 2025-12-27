import asyncio
import os
from dotenv import load_dotenv

from src.application.services.vector_service import VectorService, VectorBackend
from src.infrastructure.repositories import ArticleRepository
from src.infrastructure.database.session import get_async_session


async def main():
    load_dotenv()

    backend = os.getenv("VECTOR_BACKEND", "faiss").lower()
    query = os.getenv("TEST_QUERY", "увольнение")

    if backend == "postgres":
        v_user = os.getenv("VECTOR_DB_USER", os.getenv("POSTGRES_USER", "postgres"))
        v_password = os.getenv(
            "VECTOR_DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        v_host = os.getenv("VECTOR_DB_HOST", os.getenv("POSTGRES_HOST", "localhost"))
        v_port = os.getenv("VECTOR_DB_PORT", os.getenv("POSTGRES_PORT", "5432"))
        v_name = os.getenv(
            "VECTOR_DB_NAME", os.getenv("POSTGRES_DB", "legal_agent_vectors")
        )
        conn_str = f"postgresql://{v_user}:{v_password}@{v_host}:{v_port}/{v_name}"
        vector_service = VectorService(
            backend=VectorBackend.POSTGRES, connection_string=conn_str
        )
    else:
        vector_service = VectorService(backend=VectorBackend.FAISS)

    # Try to load FAISS index if available
    if backend == "faiss":
        index_path = os.getenv("VECTOR_INDEX_PATH", "data/faiss_index")
        try:
            await vector_service.load_index(index_path)
            print(f"Loaded FAISS index from {index_path}")
        except Exception as e:
            print(
                f"FAISS index not found or failed to load: {e}\nWill build index from DB..."
            )
            # build from DB
            async for session in get_async_session():
                repo = ArticleRepository(session)
                articles = await repo.get_all(limit=5000, offset=0)
                await vector_service.build_index(articles)
                await vector_service.save_index(index_path)
                break
    else:
        # For Postgres, ensure vectors exist by building from DB
        async for session in get_async_session():
            repo = ArticleRepository(session)
            articles = await repo.get_all(limit=5000, offset=0)
            await vector_service.build_index(articles)
            break

    # Run semantic search
    try:
        results = await vector_service.find_similar(query, top_k=5)
        print(f"\nTop results for query: '{query}'\n")
        for a in results:
            print(f"{a.number} — {a.title}\n{a.content[:200].strip()}...\n")
    except Exception as e:
        print(f"Search failed: {e}")

    await vector_service.close()


if __name__ == "__main__":
    asyncio.run(main())
