from typing import TypedDict, List, Dict, Any


class RAGState(TypedDict):

    # user query
    query: str

    # sql retrieval output
    sql_context: Dict[str, Any]

    # retrieval outputs
    vector_docs: List
    fts_docs: List
    hybrid_docs: List
    reranked_docs: List

    # merged context
    final_context: str

    # final response
    response: Dict[str, Any]

    # evaluation
    retry_count: int
