import os

from dotenv import load_dotenv

from typing import Literal

from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.api.v1.states.rag_state import RAGState

from src.api.v1.tools.sql_retrieval_tool import sql_retrieval_node

from src.api.v1.tools.hybrid_search_tool import hybrid_search_node

from src.api.v1.tools.rerank_tool import rerank_node

from src.api.v1.tools.context_builder_tool import context_builder_node

from src.api.v1.schemas.query_schema import AIResponse

load_dotenv()


def get_llm():

    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
    )


# ---------------------------------------------------------
# INTENT NODE
# ---------------------------------------------------------


class IntentDecision(BaseModel):

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
                Analyze the user's question.

                Determine:

                need_sql:
                    True if customer data,
                    transactions,
                    rewards,
                    statements,
                    spending,
                    fee waiver progress,
                    international spend,
                    MoM comparison are needed.

                need_rag:
                    True if card features,
                    rewards policy,
                    redemption rules,
                    billing rules,
                    forex rules,
                    fee waiver policy,
                    credit card benefits are needed.

                Most queries may require BOTH.

                Return decision only.
                """,
            ),
            (
                "human",
                """
                Query:

                {query}
                """,
            ),
        ]
    )

    chain = prompt | structured_llm

    decision = chain.invoke({"query": state["query"]})

    print(decision)

    return {**state, "intent": decision.model_dump()}


# ---------------------------------------------------------
# SUMMARY NODE
# ---------------------------------------------------------


def summary_node(state: RAGState):

    print("=== SUMMARY NODE ===")

    llm = get_llm()

    structured_llm = llm.with_structured_output(AIResponse)

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

    return {**state, "response": response.model_dump()}


# ---------------------------------------------------------
# EVALUATE NODE
# ---------------------------------------------------------


def evaluate_node(state: RAGState):

    print("=== EVALUATE NODE ===")

    response = state["response"]

    answer = response.get("answer", "")

    retry_count = state.get("retry_count", 0)

    evaluation_result = {"passed": True, "reason": "Validation passed"}

    if len(answer.strip()) < 20:

        evaluation_result = {"passed": False, "reason": "Answer too short"}

    return {
        **state,
        "evaluation_result": evaluation_result,
        "retry_count": retry_count + 1,
    }


# ---------------------------------------------------------
# CONDITIONAL EDGE
# ---------------------------------------------------------


def evaluation_router(state: RAGState):

    evaluation = state["evaluation_result"]

    retry_count = state["retry_count"]

    if evaluation["passed"] is False and retry_count < 2:
        return "retry"

    return "pass"


# ---------------------------------------------------------
# BUILD GRAPH
# ---------------------------------------------------------


def build_credit_card_graph():

    workflow = StateGraph(RAGState)

    workflow.add_node("intent", intent_node)

    workflow.add_node("sql_retrieval", sql_retrieval_node)

    workflow.add_node("hybrid_search", hybrid_search_node)

    workflow.add_node("rerank", rerank_node)

    workflow.add_node("context_builder", context_builder_node)

    workflow.add_node("summary", summary_node)

    workflow.add_node("evaluate", evaluate_node)

    workflow.set_entry_point("intent")

    workflow.add_edge("intent", "sql_retrieval")

    workflow.add_edge("sql_retrieval", "hybrid_search")

    workflow.add_edge("hybrid_search", "rerank")

    workflow.add_edge("rerank", "context_builder")

    workflow.add_edge("context_builder", "summary")

    workflow.add_edge("summary", "evaluate")

    workflow.add_conditional_edges(
        "evaluate", evaluation_router, {"retry": "summary", "pass": END}
    )

    memory = MemorySaver()

    graph = workflow.compile(checkpointer=memory)

    return graph


credit_card_graph = build_credit_card_graph()


# ---------------------------------------------------------
# EXECUTION METHOD
# ---------------------------------------------------------


def run_credit_card_agent(query: str, card_id: str | None = None, billing_month: str | None = None, thread_id: str = "default"):

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
