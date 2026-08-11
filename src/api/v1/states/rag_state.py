from typing import Any, Dict, List, TypedDict

from langchain_core.documents import Document


class RAGState(TypedDict, total=False):

    query: str

    card_id: str

    billing_month: str

    intent: Dict[str, Any]

    sql_context: Dict[str, Any]

    vector_docs: List[Document]

    fts_docs: List[Document]

    hybrid_docs: List[Document]

    reranked_docs: List[Document]

    final_context: str

    response: Dict[str, Any]

    evaluation_result: Dict[str, Any]

    retry_count: int