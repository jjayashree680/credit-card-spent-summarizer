import os
import cohere


def rerank_node(state):

    print("===== RERANK =====")

    co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))

    docs = state["hybrid_docs"]

    reranked = co.rerank(
        model="rerank-v3.5",
        query=state["query"],
        documents=[doc.page_content for doc in docs],
        top_n=5,
    )

    reranked_docs = [docs[result.index] for result in reranked.results]

    return {**state, "reranked_docs": reranked_docs}
