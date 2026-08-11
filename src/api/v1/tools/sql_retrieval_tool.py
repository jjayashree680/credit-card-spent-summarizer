import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.core.db import get_sql_database

load_dotenv()


def get_llm():

    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
    )


def classify_sql_request(query: str):
    """
    Simple query classifier.
    Decides whether to use
    Structured Retrieval or NL2SQL.
    """

    analytics_keywords = [
        "summary",
        "spend",
        "reward",
        "international",
        "merchant",
        "category",
        "billing",
        "statement",
        "month",
        "compare",
        "waiver",
    ]

    query_lower = query.lower()

    for keyword in analytics_keywords:

        if keyword in query_lower:
            return "ANALYTICS"

    return "NL2SQL"


def nl2sql(query: str):

    db = get_sql_database()

    llm = get_llm()

    schema = db.get_table_info()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are an expert PostgreSQL assistant.

                Generate ONLY SELECT statements.

                Rules:
                - Return SQL only.
                - No markdown.
                - No explanation.
                - No INSERT.
                - No UPDATE.
                - No DELETE.
                - No DROP.

                Database Schema:

                {schema}
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

    chain = prompt | llm

    result = chain.invoke({"schema": schema, "query": query})

    sql_query = result.content.strip()

    sql_result = db.run(sql_query)

    return {
        "retrieval_type": "NL2SQL",
        "generated_sql": sql_query,
        "sql_result": sql_result,
    }


def analytics_retrieval(query: str):

    db = get_sql_database()

    analytics_context = {}

    #
    # Total Spend
    #
    try:

        analytics_context["total_spend"] = db.run("""
            SELECT
                SUM(amount)
            FROM card_transactions
            WHERE txn_type = 'purchase';
            """)

    except Exception as e:

        analytics_context["total_spend"] = str(e)

    #
    # Top Categories
    #
    try:

        analytics_context["top_categories"] = db.run("""
            SELECT
                category,
                SUM(amount) AS spend
            FROM card_transactions
            GROUP BY category
            ORDER BY spend DESC
            LIMIT 5;
            """)

    except Exception as e:

        analytics_context["top_categories"] = str(e)

    #
    # Top Merchants
    #
    try:

        analytics_context["top_merchants"] = db.run("""
            SELECT
                merchant_name,
                SUM(amount) AS spend
            FROM card_transactions
            GROUP BY merchant_name
            ORDER BY spend DESC
            LIMIT 5;
            """)

    except Exception as e:

        analytics_context["top_merchants"] = str(e)

    #
    # International Spend
    #
    try:

        analytics_context["international_spend"] = db.run("""
            SELECT
                COUNT(*) AS txn_count,
                SUM(amount) AS spend
            FROM card_transactions
            WHERE is_international = TRUE;
            """)

    except Exception as e:

        analytics_context["international_spend"] = str(e)

    #
    # Rewards
    #
    try:

        analytics_context["reward_points"] = db.run("""
            SELECT
                SUM(points_earned)
            FROM reward_transactions;
            """)

    except Exception as e:

        analytics_context["reward_points"] = str(e)

    return {"retrieval_type": "ANALYTICS", "analytics_context": analytics_context}


def sql_retrieval_node(state):

    print("===== SQL RETRIEVAL =====")

    query = state["query"]

    retrieval_type = classify_sql_request(query)

    if retrieval_type == "ANALYTICS":

        sql_context = analytics_retrieval(query)

    else:

        sql_context = nl2sql(query)

    return {**state, "sql_context": sql_context}
