import os
import re

from dotenv import load_dotenv

from datetime import datetime


import re


from typing import Literal
import time

from pydantic import BaseModel

from typing import Optional, Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# from src.api.v1.tools.guardrails_tool import guardrails_node

from src.core.guardrails import guard_output
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
        model=os.getenv("OPENAI_CHAT_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True,
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


def extract_user_name(query: str):

    match = re.search(
        r"(?:i am|i'm|my name is|this is|call me)\s+([A-Za-z]+)",
        query,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def conversational_node(state: RAGState):

    print("=== CONVERSATIONAL NODE ===")

    query = state["query"]

    intent = state.get("intent", {})
    query_type = intent.get("query_type", "")

    user_name = state.get("user_name")
    print("USER NAME =", state.get("user_name"))

    lower_query = query.lower().strip()

    # --------------------------------------------------
    # Remember user identity
    # --------------------------------------------------

    if "who am i" in lower_query or "what is my name" in lower_query:
        if user_name:
            answer = f"You're {user_name}!"
        else:
            answer = (
                "I don't know your name yet. "
                "You can tell me by saying "
                "'I am <your name>'."
            )

        return {
            **state,
            "response": {
                "query": query,
                "answer": answer,
                "policy_citations": "",
                "page_no": "",
                "document_name": "",
                "sql_query_executed": None,
            },
        }

    # --------------------------------------------------
    # Out of Scope
    # --------------------------------------------------

    if query_type == "out_of_scope":

        answer = (
            "I'm specifically designed to assist with "
            "credit card spending analysis, rewards, "
            "transactions, billing statements and "
            "card-related policies."
        )

        return {
            **state,
            "response": {
                "query": query,
                "answer": answer,
                "policy_citations": "",
                "page_no": "",
                "document_name": "",
                "sql_query_executed": None,
            },
        }

    # --------------------------------------------------
    # Chit Chat
    # --------------------------------------------------

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
You are a friendly conversational assistant.

Known user name:
{user_name}

Rules:
- Be warm and friendly.
- Keep response concise.
- Do not repeat introductions.
- Use the user's name when appropriate.
- If user already told their name, remember it.
- Do not bring up credit cards unless user asks.
""",
            ),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm

    response = chain.invoke({"query": query})

    return {
        **state,
        "response": {
            "query": query,
            "answer": response.content,
            "policy_citations": "",
            "page_no": "",
            "document_name": "",
            "sql_query_executed": None,
        },
    }


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

Classify every user query into exactly one of:

1. credit_card

Use credit_card for questions related to:

- transactions
- rewards
- reward points
- fee waiver
- billing statements
- spend summary
- international spend
- category spend
- top merchants
- card policies
- card details
- spending comparisons
- credit card charges

2. chitchat

Use chitchat for normal conversation such as:

- hi
- hello
- hey
- hi there
- how are you
- how r you
- how are u
- good morning
- good afternoon
- good evening
- thanks
- thank you
- bye
- see you
- help me
- can you help me
- i am Fathima
- my name is Fathima
- nice to meet you
- what can you do
- what are you doing
- who are you
- how is your day

These should NOT require SQL or RAG.

3. out_of_scope

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
Use out_of_scope for requests unrelated to the credit card assistant, including:

- cooking
- recipes
- chocolate recipes
- sports
- politics
- weather
- coding
- movies
- travel planning
- general programming
- how to attack someone
- how to hurt someone
- requests to harm another person
- other unrelated requests

These should NOT require SQL or RAG.

IMPORTANT:

A casual statement such as:

"I am Fathima"
"My name is Fathima"

is chitchat.

A question such as:

"Who am I?"

is also chitchat unless the user is explicitly asking for a verified customer identity lookup.

If the user provides a card ID or billing month, extract them.

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
Conversation History:

{chat_history}

Current User Query:

{query}                """,
            ),
        ]
    )

    chain = prompt | structured_llm

    decision = chain.invoke(
        {
            "query": state["query"],
            "chat_history": state.get(
                "chat_history",
                [],
            ),
        }
    )
    card_id = decision.card_id

    billing_month = decision.billing_month
    history = state.get("chat_history", [])

    if not card_id:

        for message in reversed(history):

            if message["role"] != "user":
                continue

            content = message.get("content", "")

            match = re.search(
                r"CC-\d+",
                content,
                re.IGNORECASE,
            )

            if match:

                card_id = match.group()

                print(
                    "RECOVERED CARD ID =",
                    card_id,
                )

                break

    if not billing_month:

        month_map = {
            "january": "01",
            "february": "02",
            "march": "03",
            "april": "04",
            "may": "05",
            "june": "06",
            "july": "07",
            "august": "08",
            "september": "09",
            "october": "10",
            "november": "11",
            "december": "12",
        }

        for message in reversed(history):

            if message.get("role") != "user":
                continue

            content = message.get("content", "")

            # Already in YYYY-MM format
            match = re.search(
                r"\b(20\d{2}-\d{2})\b",
                content,
            )

            if match:

                billing_month = match.group(1)

                print(
                    "RECOVERED BILLING MONTH =",
                    billing_month,
                )

                break

            # Month Year format (e.g. March 2026)
            month_match = re.search(
                r"\b("
                r"January|February|March|April|May|June|"
                r"July|August|September|October|November|December"
                r")\s+(20\d{2})\b",
                content,
                re.IGNORECASE,
            )

            if month_match:

                month_name = month_match.group(1).lower()
                year = month_match.group(2)

                billing_month = f"{year}-{month_map[month_name]}"

                print(
                    "RECOVERED BILLING MONTH =",
                    billing_month,
                )

                break
    history = state.get("chat_history", [])

    # Recover card id from previous conversation

    # if not card_id:

    #     for message in reversed(history):

    #         content = message.get("content", "")

    #         match = re.search(
    #             r"CC-\d+",
    #             content,
    #             re.IGNORECASE,
    #         )

    #         if match:

    #             card_id = match.group()

    #             print(
    #                 "RECOVERED CARD ID =",
    #                 card_id,
    #             )

    #             break

    print("RETRIEVAL TYPE =", decision.retrieval_type)

    print(decision)

    # =====================================================
    # IMPORTANT
    # ALWAYS SAVE INTENT INTO STATE
    # =====================================================

    intent_data = decision.model_dump()

    print(f"Saved intent: {intent_data}")

    # =====================================================
    # CHITCHAT
    # =====================================================

    # if decision.query_type == "chitchat":

    #     return {
    #         **state,

    #         # THIS WAS MISSING
    #         "intent": intent_data,

    #         "response": {
    #             "query": state["query"],
    #             "answer": (
    #                 "Hello! I'm your Credit Card Spend Assistant. "
    #                 "I can help with spending analysis, rewards, "
    #                 "transactions, billing statements, fee waiver "
    #                 "eligibility, and international spend."
    #             ),
    #             "policy_citations": "",
    #             "page_no": "",
    #             "document_name": "",
    #             "sql_query_executed": None,
    #         },
    #     }
    user_name = state.get("user_name")

    if not user_name:

        history = state.get("chat_history", [])

        print("CHAT HISTORY =", history)

        for message in reversed(history):

            if message["role"] != "user":
                continue

            detected = extract_user_name(message["content"])

            if detected:

                print("FOUND NAME IN HISTORY =", detected)

                user_name = detected

                break

    print("FINAL USER NAME =", user_name)

    # detected_name = extract_user_name(state["query"])

    # if detected_name:
    #     user_name = detected_name
    # print("DETECTED NAME =", detected_name)
    # print("CURRENT USER NAME =", user_name)
    print("CHAT HISTORY =", state.get("chat_history"))
    if decision.query_type == "chitchat":
        return {
            **state,
            "intent": intent_data,
            "user_name": user_name,
        }

    # =====================================================
    # OUT OF SCOPE
    # =====================================================

    if decision.query_type == "out_of_scope":

        return {
            **state,
            "intent": intent_data,
            "user_name": user_name,
        }

    # =====================================================
    # CREDIT CARD QUERY
    # =====================================================

    query_lower = state["query"].lower()

    needs_card_context = any(
        keyword in query_lower
        for keyword in [
            "my spend",
            "my spending",
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
        and not state.get("card_id")
    ):

        return {
            **state,
            "intent": intent_data,
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

    # =====================================================
    # CREDIT CARD QUERY CONTINUES TO SQL/RAG
    # =====================================================
    print("###############")
    print("FINAL CARD ID =", card_id)
    print("FINAL BILLING MONTH =", billing_month)
    print("###############")

    # return {
    #     **state,
    #     "user_name": user_name,
    #     "card_id": card_id or state.get("card_id"),
    #     "billing_month": (decision.billing_month or state.get("billing_month")),
    #     "intent": intent_data,
    # }
    return {
        **state,
        "user_name": user_name,
        "card_id": card_id or state.get("card_id"),
        "billing_month": billing_month or state.get("billing_month"),
        "intent": intent_data,
    }


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

1. SQL Context is the source of truth.
2. Never modify SQL-derived values.
3. Never invent numbers, percentages, dates, or facts.
4. Use Knowledge Base (KB) Context only for explanations and policy guidance.
5. Always provide citations.
6. Mention rewards, forex, and fee-waiver status only when relevant.
7. Do not use markdown tables.

RESPONSE STYLE RULES

- Match the response detail to the user's question.
- For simple factual questions, provide a concise answer.
- For summary, comparison, spend analysis, billing statement, transaction analysis, rewards analysis, and fee-waiver assessments, provide detailed responses with sections and bullet points.
- Do not generate lengthy reports for simple questions.
- Use only the amount of information needed to answer the question clearly.

FORMATTING RULES

For summary or analytics questions:
- Use markdown headings.
- Use markdown bullet points.
- Use separate sections.
- Use clear labels and values.
- Every category should be a bullet point.
- Every merchant should be a bullet point.

For direct factual questions:
- Answer in 1 to 5 sentences.
- Do not create multiple sections unless necessary.
- Use bullet points only when they improve clarity.

EXAMPLE 1

User:
What is the annual membership fee?

Response:

The annual membership fee for the NorthStar Gold card is Rs. 999 + GST.

Citation: NorthStar Bank Credit Card Product Guide.

EXAMPLE 2

User:
What did I spend the most on last month?

Response:

You spent the most on Travel in March 2026.

- Amount: Rs. 40,900.00
- Transactions: 2

Citation: SQL query result.

EXAMPLE 3

User:
Summarise my spending for March 2026.

Response:

## Spend Summary

- Total Spend: Rs. 106,800.00
- Reward Points Earned: 1,550
- International Spend: Rs. 50,900.00

## Category Breakdown

- Travel: Rs. 40,900.00
- Shopping: Rs. 30,500.00
- Jewellery: Rs. 9,800.00

## Top Merchants

- Singapore Airlines: Rs. 32,400.00
- Amazon UK: Rs. 18,500.00

Citation: SQL query result.
            """,
            ),
            (
                "human",
                """
Conversation History:
{chat_history}

Current User Query:
{query}

Context:
{context}
            """,
            ),
        ]
    )

    chain = prompt | structured_llm

    response = chain.invoke(
        {
            "query": state["query"],
            "context": state["final_context"],
            "chat_history": state.get(
                "chat_history",
                [],
            ),
        }
    )

    return {
        **state,
        "response": response.model_dump(),
        "retry_count": state.get("retry_count", 0) + 1,
    }


# ---------------------------------------------------------
# STREAMING SUMMARY
# ---------------------------------------------------------


def stream_summary(
    query: str,
    context: str,
    chat_history: list,
):

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a Credit Card Spend Intelligence Assistant.

Rules:
- Use only the supplied context.
- Do not invent information.
- Answer directly.
- Be concise.
- Avoid repetition.
- Do not use markdown tables.
- Use bullet points when listing multiple items.
- Keep explanations easy to read.
            """,
            ),
            (
                "human",
                """
Conversation History:
{chat_history}

Current Query:
{query}

Context:
{context}
                """,
            ),
        ]
    )

    chain = prompt | llm

    for chunk in chain.stream(
        {
            "query": query,
            "context": context,
            "chat_history": chat_history,
        }
    ):
        if hasattr(chunk, "content") and chunk.content:
            yield chunk.content


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


# def evaluation_router(state: RAGState):

#     evaluation = state["evaluation_result"]

#     retry_count = state["retry_count"]

#     print(f"passed={evaluation['passed']} " f"retry_count={retry_count}")

#     if evaluation["passed"] is False and retry_count < 2:
#         return "retry"

#     return "pass"


def evaluation_router(state: RAGState):

    evaluation = state.get("evaluation_result")

    if not evaluation:
        print("evaluation_result missing")
        return "pass"

    retry_count = state.get("retry_count", 0)

    print(f"passed={evaluation['passed']} " f"retry_count={retry_count}")

    if evaluation["passed"] is False and retry_count < 2:
        return "retry"

    return "pass"


def intent_router(state: RAGState):

    intent = state.get("intent", {})

    query_type = intent.get("query_type", "")

    print(f"Routing query_type: {query_type}")

    # -----------------------------------------
    # CHITCHAT
    # -----------------------------------------

    if query_type == "chitchat":
        return "conversation"

    # -----------------------------------------
    # OUT OF SCOPE
    # -----------------------------------------

    if query_type == "out_of_scope":
        return "conversation"

    # -----------------------------------------
    # CREDIT CARD
    # -----------------------------------------

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

    return "conversation"


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
    workflow.add_node("conversation", conversational_node)

    workflow.set_entry_point("intent")

    workflow.add_conditional_edges(
        "intent",
        intent_router,
        {
            "conversation": "conversation",
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
    workflow.add_edge("conversation", END)

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
    chat_history: list | None = None,
):

    initial_state = {
        "query": query,
        "card_id": card_id,
        "billing_month": billing_month,
        "user_name": None,
        "sql_context": {},
        "vector_docs": [],
        "fts_docs": [],
        "hybrid_docs": [],
        "reranked_docs": [],
        "final_context": "",
        "response": {},
        "retry_count": 0,
        "chat_history": chat_history or [],
    }

    final_state = credit_card_graph.invoke(
        initial_state, config={"configurable": {"thread_id": thread_id}}
    )
    # context = final_state["final_context"]

    # yield from stream_summary(
    #     query=query,
    #     context=context,
    # )

    return final_state["response"]


def run_credit_card_agent_stream(
    query: str,
    card_id: str | None = None,
    billing_month: str | None = None,
    thread_id: str = "default",
    chat_history: list | None = None,
):

    initial_state = {
        "query": query,
        "card_id": card_id,
        "billing_month": billing_month,
        "chat_history": chat_history or [],
        "user_name": None,
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
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
    )
    answer = final_state["response"]["answer"]

    print("===== ANSWER REPR =====")

    print(repr(answer))

    print("===== ANSWER REPR =====")
    answer = guard_output(answer)

    answer = answer.replace("<br>", "\n")

    chunk_size = 30

    for i in range(0, len(answer), chunk_size):
        yield answer[i : i + chunk_size]
        time.sleep(0.02)
    # yield from stream_summary(
    #     query=query,
    #     context=final_state["final_context"],
    #     chat_history=chat_history or [],
    # )
