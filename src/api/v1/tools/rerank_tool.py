import os

import cohere

from dotenv import load_dotenv


load_dotenv()


def rerank_node(state):

    print("===== RERANK =====")

    co = cohere.ClientV2(
        api_key=os.getenv("COHERE_API_KEY")
    )

    docs = state.get("hybrid_docs", [])

    if not docs:
        return {
            **state,
            "reranked_docs": [],
        }

    reranked = co.rerank(
        model="rerank-v3.5",
        query=state["query"],
        documents=[
            doc.page_content
            for doc in docs
        ],
        top_n=min(5, len(docs)),
    )

    reranked_docs = [
        docs[result.index]
        for result in reranked.results
    ]

    print(
        f"Reranked {len(docs)} docs → "
        f"Top {len(reranked_docs)}"
    )

    return {
        **state,
        "reranked_docs": reranked_docs,
    }