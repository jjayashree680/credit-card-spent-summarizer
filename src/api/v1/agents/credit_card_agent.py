import os

from dotenv import load_dotenv

from typing import Literal

from pydantic import BaseModel

from typing import Optional, Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# from src.api.v1.tools.guardrails_tool import guardrails_node

from src.api.v1.states.rag_state import RAGState

from src.api.v1.tools.sql_retrieval_tool import sql_retrieval_node

from src.api.v1.tools.hybrid_search_tool import hybrid_search_node
from src.api.v1.tools.fts_search_tool import fts_search_node
from src.api.v1.tools.vector_search_tool import vector_search_node

from src.api.v1.tools.rerank_tool import rerank_node


from src.api.v1.tools.context_builder_tool import context_builder_node

from src.api.v1.schemas.query_schema import QueryResponse

load_dotenv()


def get_llm():

    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
    )


# ---------------------------------------------------------
# INTENT NODE
# ---------------------------------------------------------


class IntentDecision(BaseModel):

    query_type: Literal[
        "credit_card",
        "chitchat",
        "out_of_scope",
    ]

    retrieval_type: Literal[
        "vector",
        "fts",
        "hybrid",
    ] = "hybrid"

    card_id: Optional[str] = None

    billing_month: Optional[str] = None

    need_sql: bool

    need_rag: bool

    reason: str


def intent_node(state: RAGState):

    print("=== INTENT NODE ===")

    llm = get_llm()

    structured_llm = llm.with_structured_output(IntentDecision)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a Credit Card Spend Assistant.

Classify every query into one of:

1. credit_card
   - transactions
   - rewards
   - fee waiver
   - billing statements
   - spend summary
   - international spend
   - category spend
   - top merchants
   - card policies

2. chitchat
   - hi
   - hello
   - good morning
   - good evening
   - thank you
   - bye
   - how are you

3. out_of_scope
   - cooking
   - recipes
   - sports
   - politics
   - weather
   - coding
   - movies
   - travel planning
   - anything unrelated to credit cards

For retrieval_type:

Use "fts" when:
- query contains exact policy terms
- annual membership fee
- fee waiver eligibility
- forex markup fee
- minimum amount due
- billing cycle
- cash withdrawal limit

Use "vector" when:
- query is conceptual
- query is paraphrased
- query asks "how", "why", "explain"

Use "hybrid" when:
- both semantic understanding and keyword matching are beneficial

Return:
query_type
retrieval_type
need_sql
need_rag
reason

If the user provides a card id or billing month,
extract them.

Examples:

User:
Summarise spend details on card id C00014 and month March 2026

card_id = C00014
billing_month = 2026-03

User:
Show transactions for CC-881001

card_id = CC-881001
billing_month = null

Rules:

- credit_card -> need_sql and/or need_rag as required
- chitchat -> need_sql=False, need_rag=False
- out_of_scope -> need_sql=False, need_rag=False
                """,
            ),
            (
                "human",
                """
User Query:

{query}
                """,
            ),
        ]
    )

    chain = prompt | structured_llm

    decision = chain.invoke({"query": state["query"]})

    print("RETRIEVAL TYPE =", decision.retrieval_type)

    print(decision)

    # --------------------------
    # CHITCHAT
    # --------------------------

    if decision.query_type == "chitchat":

        return {
            **state,
            "response": {
                "query": state["query"],
                "answer": (
                    "Hello! I'm your Credit Card Spend Assistant. "
                    "I can help with spending analysis, rewards, "
                    "transactions, billing statements, fee waiver "
                    "eligibility and international spend."
                ),
                "policy_citations": "",
                "page_no": "",
                "document_name": "",
                "sql_query_executed": None,
            },
        }

    # --------------------------
    # OUT OF SCOPE
    # --------------------------

    if decision.query_type == "out_of_scope":

        return {
            **state,
            "response": {
                "query": state["query"],
                "answer": (
                    "I'm specifically designed to assist with "
                    "credit card spending analysis, rewards, "
                    "transactions, billing statements and "
                    "card-related policies. "
                    "I cannot assist with unrelated topics."
                ),
                "policy_citations": "",
                "page_no": "",
                "document_name": "",
                "sql_query_executed": None,
            },
        }

    # --------------------------
    # MISSING CARD DETAILS
    # --------------------------

    query_lower = state["query"].lower()

    # needs_card_context = any(
    #     keyword in query_lower
    #     for keyword in [
    #         "spend",
    #         "transaction",
    #         "reward",
    #         "statement",
    #         "billing",
    #         "fee waiver",
    #         "top merchant",
    #         "international",
    #     ]
    # )
    needs_card_context = any(
        keyword in query_lower
        for keyword in [
            "my spend",
            "my transactions",
            "my rewards",
            "what did i spend",
            "show my transactions",
            "my billing statement",
            "my card",
            "top merchant on my card",
        ]
    )

    if (
        decision.query_type == "credit_card"
        and needs_card_context
        and not decision.card_id
    ):

        return {
            **state,
            "response": {
                "query": state["query"],
                "answer": (
                    "Please provide a card ID so that I can "
                    "retrieve the requested spending information."
                ),
                "policy_citations": "",
                "page_no": "",
                "document_name": "",
                "sql_query_executed": None,
            },
        }
    # --------------------------
    # CREDIT CARD QUERY
    # --------------------------

    # --------------------------
    # CREDIT CARD QUERY
    # --------------------------

    return {
        **state,
        "card_id": decision.card_id or state.get("card_id"),
        "billing_month": (decision.billing_month or state.get("billing_month")),
        "intent": decision.model_dump(),
    }


# def vector_search_node(state: RAGState):

#     print("=== VECTOR SEARCH ===")

#     vector_docs = vector_search(state["query"])

#     return {
#         **state,
#         "vector_docs": vector_docs,
#         "hybrid_docs": vector_docs,
#     }


# def fts_search_node(state: RAGState):

#     print("=== FTS SEARCH ===")

#     fts_docs = fts_search(state["query"])

#     return {
#         **state,
#         "fts_docs": fts_docs,
#         "hybrid_docs": fts_docs,
#     }


# ---------------------------------------------------------
# SUMMARY NODE
# ---------------------------------------------------------


def summary_node(state: RAGState):

    print("=== SUMMARY NODE ===")

    llm = get_llm()

    structured_llm = llm.with_structured_output(QueryResponse)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a Credit Card Spend Intelligence Assistant.

                RULES

                1. SQL Context contains the source of truth.
                2. Never change SQL derived values.
                3. Never invent numbers.
                4. Use KB Context only for explanations.
                5. Always provide citations.
                6. Mention rewards, forex, fee waiver status
                   when relevant.
                Do not use markdown tables.

                Return information using plain text and bullet points.
                """,
            ),
            (
                "human",
                """
                User Query:
                {query}

                Context:
                {context}
                """,
            ),
        ]
    )

    chain = prompt | structured_llm

    response = chain.invoke(
        {"query": state["query"], "context": state["final_context"]}
    )

    return {
        **state,
        "response": response.model_dump(),
        "retry_count": state.get("retry_count", 0) + 1,
    }


# ---------------------------------------------------------
# EVALUATE NODE
# ---------------------------------------------------------


def evaluate_node(state):

    print("===== EVALUATE =====")

    response = state.get("response", {})
    answer = response.get("answer", "")

    sql_context = state.get("sql_context", {})
    reranked_docs = state.get("reranked_docs", [])

    intent = state.get("intent", {})

    need_sql = intent.get("need_sql", False)
    need_rag = intent.get("need_rag", False)

    checks = []

    checks.append(len(answer.strip()) > 20)

    if need_sql:
        checks.append(bool(sql_context))
        checks.append(bool(sql_context.get("generated_sql")))

    if need_rag:
        checks.append(len(reranked_docs) > 0)

    passed = all(checks)

    return {
        **state,
        "evaluation_result": {
            "passed": passed,
            "reason": ("Validation Passed" if passed else "Validation Failed"),
        },
    }


# CONDITIONAL EDGE
# ---------------------------------------------------------


def evaluation_router(state: RAGState):

    evaluation = state["evaluation_result"]

    retry_count = state["retry_count"]

    print(f"passed={evaluation['passed']} " f"retry_count={retry_count}")

    if evaluation["passed"] is False and retry_count < 2:
        return "retry"

    return "pass"


def intent_router(state: RAGState):

    if state.get("response"):
        return "end"

    intent = state.get("intent", {})

    need_sql = intent.get("need_sql", False)
    need_rag = intent.get("need_rag", False)

    retrieval_type = intent.get(
        "retrieval_type",
        "hybrid",
    )

    if need_sql:
        return "sql"

    if need_rag:
        return retrieval_type

    return "end"


# ---------------------------------------------------------
# BUILD GRAPH
# ---------------------------------------------------------


def build_credit_card_graph():

    workflow = StateGraph(RAGState)

    workflow.add_node("intent", intent_node)

    workflow.add_node("sql_retrieval", sql_retrieval_node)
    workflow.add_node(
        "vector_search",
        vector_search_node,
    )

    workflow.add_node(
        "fts_search",
        fts_search_node,
    )

    workflow.add_node(
        "hybrid_search",
        hybrid_search_node,
    )

    # workflow.add_node("hybrid_search", hybrid_search_node)

    workflow.add_node("rerank", rerank_node)

    workflow.add_node("context_builder", context_builder_node)

    workflow.add_node("summary", summary_node)

    workflow.add_node("evaluate", evaluate_node)

    # workflow.add_node("guardrails", guardrails_node)

    workflow.set_entry_point("intent")

    workflow.add_conditional_edges(
        "intent",
        intent_router,
        {
            "sql": "sql_retrieval",
            "vector": "vector_search",
            "fts": "fts_search",
            "hybrid": "hybrid_search",
            "end": END,
        },
    )
    workflow.add_edge("sql_retrieval", "hybrid_search")
    workflow.add_edge(
        "vector_search",
        "rerank",
    )

    workflow.add_edge(
        "fts_search",
        "rerank",
    )

    workflow.add_edge(
        "hybrid_search",
        "rerank",
    )

    # workflow.add_edge("hybrid_search", "rerank")

    workflow.add_edge("rerank", "context_builder")

    workflow.add_edge("context_builder", "summary")

    workflow.add_edge("summary", "evaluate")

    workflow.add_conditional_edges(
        "evaluate",
        evaluation_router,
        {
            "retry": "summary",
            "pass": END,
        },
    )

    memory = MemorySaver()

    graph = workflow.compile(checkpointer=memory)

    return graph


credit_card_graph = build_credit_card_graph()


# ---------------------------------------------------------
# EXECUTION METHOD
# ---------------------------------------------------------


def run_credit_card_agent(
    query: str,
    card_id: str | None = None,
    billing_month: str | None = None,
    thread_id: str = "default",
):

    initial_state = {
        "query": query,
        "card_id": card_id,
        "billing_month": billing_month,
        "sql_context": {},
        "vector_docs": [],
        "fts_docs": [],
        "hybrid_docs": [],
        "reranked_docs": [],
        "final_context": "",
        "response": {},
        "retry_count": 0,
    }

    final_state = credit_card_graph.invoke(
        initial_state, config={"configurable": {"thread_id": thread_id}}
    )

    return final_state["response"]
