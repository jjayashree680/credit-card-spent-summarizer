import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_core.documents import Document

load_dotenv()

engine = create_engine(os.getenv("PG_CONNECTION_STRING"))


def fts_search(
    query: str,
    limit: int = 20,
):

    sql = text("""
        SELECT
            document,
            cmetadata
        FROM langchain_pg_embedding
        WHERE to_tsvector('english', document)
        @@ plainto_tsquery('english', :query)
        LIMIT :limit
        """)

    docs = []

    with engine.connect() as conn:

        results = conn.execute(
            sql,
            {
                "query": query,
                "limit": limit,
            },
        )

        for row in results:

            docs.append(
                Document(
                    page_content=row.document,
                    metadata=row.cmetadata or {},
                )
            )

    return docs
