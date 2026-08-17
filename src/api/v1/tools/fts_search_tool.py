import os
import re

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_core.documents import Document
from src.api.v1.states.rag_state import RAGState

load_dotenv()

engine = create_engine(os.getenv("PG_CONNECTION_STRING"))


def preprocess_fts_query(query: str) -> str:

    query = query.lower()

    stop_phrases = [
        "what is",
        "what are",
        "tell me",
        "explain",
        "can you explain",
        "please explain",
        "how does",
        "how do",
        "show me",
        "?",
    ]

    for phrase in stop_phrases:
        query = query.replace(phrase, "")

    # Domain-specific replacements

    query = query.replace(
        "annual membership fee",
        "annual fee",
    )

    query = query.replace(
        "membership fee",
        "annual fee",
    )

    query = query.replace(
        "fee waiver eligibility criteria",
        "fee waiver",
    )

    query = query.replace(
        "foreign exchange fee",
        "forex markup",
    )

    query = re.sub(r"\s+", " ", query)

    return query.strip()


def fts_search(
    query: str,
    limit: int = 20,
):

    cleaned_query = preprocess_fts_query(query)

    print("ORIGINAL QUERY =", query)
    print("FTS QUERY =", cleaned_query)

    sql = text("""
        SELECT
            document,
            cmetadata
        FROM langchain_pg_embedding
        WHERE to_tsvector(
            'english',
            document
        )
        @@ websearch_to_tsquery(
            'english',
            :query
)
        LIMIT :limit
        """)

    docs = []

    with engine.connect() as conn:

        results = conn.execute(
            sql,
            {
                "query": cleaned_query,
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


def fts_search_node(state: RAGState):

    print("=== FTS SEARCH ===")

    docs = fts_search(
        query=state["query"],
        limit=20,
    )

    print(f"[fts_search_node] Retrieved {len(docs)} documents")

    return {
        **state,
        "fts_docs": docs,
        "hybrid_docs": docs,
    }
