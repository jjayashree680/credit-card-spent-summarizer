from typing import TypedDict, Optional


class RAGState(TypedDict, total=False):

    query: str
    card_id: Optional[str]
    billing_month: Optional[str]
    intent: dict
    user_name: Optional[str]
    sql_context: dict
    vector_docs: list
    fts_docs: list
    hybrid_docs: list
    reranked_docs: list
    final_context: str
    response: dict
    retry_count: int
    chat_history: list
    evaluation_result: dict
    role: str = "guest"
    username: str | None = None
