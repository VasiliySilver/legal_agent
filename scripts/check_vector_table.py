import asyncio
import os
from dotenv import load_dotenv

import asyncpg


async def main():
    load_dotenv()

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
    print(f"Connecting to: {conn_str}")

    conn = await asyncpg.connect(conn_str)
    try:
        # Check table existence
        tbl = await conn.fetchrow(
            """
            SELECT to_regclass('public.article_vectors') AS exists;
            """
        )
        if not tbl or tbl["exists"] is None:
            print("Table 'article_vectors' does not exist in vector DB.")
            return

        # Count rows
        row = await conn.fetchrow("SELECT COUNT(*)::int AS cnt FROM article_vectors;")
        cnt = row["cnt"] if row else 0
        print(f"Rows in article_vectors: {cnt}")

        # Distinct articles
        drow = await conn.fetchrow(
            "SELECT COUNT(DISTINCT article_id)::int AS distinct_articles FROM article_vectors;"
        )
        distinct = drow["distinct_articles"] if drow else 0
        print(f"Distinct article_id in table: {distinct}")

        # Average vectors per article
        avg_row = await conn.fetchrow(
            "SELECT AVG(cnt)::numeric(10,2) AS avg_per_article FROM (SELECT COUNT(*) AS cnt FROM article_vectors GROUP BY article_id) t;"
        )
        avg_per = (
            float(avg_row["avg_per_article"])
            if avg_row and avg_row["avg_per_article"] is not None
            else 0.0
        )
        print(f"Average vectors per article: {avg_per}")

        # Top 10 article_ids by count
        top = await conn.fetch(
            "SELECT article_id, COUNT(*) AS cnt FROM article_vectors GROUP BY article_id ORDER BY cnt DESC LIMIT 10;"
        )
        print("Top 10 article_id by vector count:")
        for r in top:
            print(dict(r))

        # Fetch sample rows
        sample = await conn.fetch(
            "SELECT id, article_id, embedding::text AS embedding_text, created_at FROM article_vectors ORDER BY id LIMIT 5;"
        )
        print("Sample rows:")
        for r in sample:
            print(dict(r))

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
