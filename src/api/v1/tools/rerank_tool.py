import os

import cohere

from dotenv import load_dotenv

# from unstructured import documents

load_dotenv()


def rerank_node(state):

    print("===== RERANK =====")

    co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))

    docs = state.get("hybrid_docs", [])

    print("DOC COUNT =", len(docs))

    for i, doc in enumerate(docs[:3]):
        print("DOC", i, "TYPE =", type(doc))

        if hasattr(doc, "page_content"):
            print("DOC", i, "PREVIEW =", doc.page_content[:200])

    if not docs:
        return {
            **state,
            "reranked_docs": [],
        }
    documents = [
        doc.page_content
        for doc in docs
        if hasattr(doc, "page_content")
        and doc.page_content
        and doc.page_content.strip()
    ]

    print("DOCUMENTS SENT TO COHERE =", len(documents))

    reranked = co.rerank(
        model="rerank-v3.5",
        query=state["query"],
        documents=documents,
        top_n=min(5, len(documents)),
    )

    reranked_docs = [docs[result.index] for result in reranked.results]

    print(f"Reranked {len(docs)} docs → " f"Top {len(reranked_docs)}")

    return {
        **state,
        "reranked_docs": reranked_docs,
    }
