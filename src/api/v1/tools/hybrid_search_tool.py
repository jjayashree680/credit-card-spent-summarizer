from src.core.db import get_vector_store
from src.api.v1.tools.fts_search_tool import fts_search


def hybrid_search_node(state):
    """
    Combines Vector Search + FTS Search.
    Removes duplicates.
    """

    query = state["query"]

    print("=== HYBRID SEARCH ===")

    vector_store = get_vector_store()

    vector_docs = vector_store.similarity_search(query=query, k=20)

    fts_docs = fts_search(query=query, limit=20)

    unique_docs = {}

    for doc in vector_docs + fts_docs:

        unique_key = doc.page_content[:200]

        unique_docs[unique_key] = doc

    hybrid_docs = list(unique_docs.values())

    print(
        f"[hybrid_search_node] "
        f"Vector={len(vector_docs)}, "
        f"FTS={len(fts_docs)}, "
        f"Merged={len(hybrid_docs)}"
    )

    return {
        **state,
        "vector_docs": vector_docs,
        "fts_docs": fts_docs,
        "hybrid_docs": hybrid_docs,
    }
