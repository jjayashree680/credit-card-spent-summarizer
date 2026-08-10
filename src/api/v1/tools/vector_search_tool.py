from src.core.db import get_vector_store


def vector_search_node(state):
    """
    Perform semantic vector search against PGVector.
    Returns top 20 matching chunks.
    """

    query = state["query"]

    print("=== VECTOR SEARCH ===")

    vector_store = get_vector_store()

    docs = vector_store.similarity_search(query=query, k=20)

    print(f"[vector_search_node] Retrieved {len(docs)} documents")

    return {**state, "vector_docs": docs}
