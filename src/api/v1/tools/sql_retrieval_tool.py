import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.core.db import get_sql_database

load_dotenv()


def get_llm():

    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
    )


def clean_sql(sql: str) -> str:

    sql = sql.strip()

    sql = sql.replace("```sql", "")

    sql = sql.replace("```", "")

    sql = sql.strip()

    sql_upper = sql.upper()

    if "WITH" in sql_upper:

        idx = sql_upper.find("WITH")

        sql = sql[idx:]

    elif "SELECT" in sql_upper:

        idx = sql_upper.find("SELECT")

        sql = sql[idx:]

    return sql.strip()


def validate_sql(sql: str):

    sql_upper = sql.strip().upper()

    allowed_prefixes = [
        "SELECT",
        "WITH",
    ]

    if not any(sql_upper.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError("Only SELECT/WITH queries are allowed.")

    blocked_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
    ]

    for keyword in blocked_keywords:

        if keyword in sql_upper:

            raise ValueError(f"{keyword} is not allowed.")


def validate_sql_result(result):

    if result is None:
        return False

    if str(result).strip() == "":
        return False

    if str(result).strip() == "[]":
        return False

    return True


def sql_retrieval_node(state):

    print("===== NL2SQL NODE =====")

    query = state["query"]

    card_id = state.get("card_id")

    billing_month = state.get("billing_month")

    db = get_sql_database()

    schema = db.get_table_info()

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a PostgreSQL expert for a Credit Card Spend Summarizer.

Available Tables:

customers
credit_cards
card_transactions
reward_transactions
billing_statements

Generate ONLY PostgreSQL SELECT statements.

Never generate:

- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- TRUNCATE
- CREATE

Important query types:

1. Spend Summary
2. Category Breakdown
3. Top Merchants
4. International Spend
5. Reward Points
6. Month-over-Month Comparison
7. Fee Waiver Eligibility

For Spend Summary requests, ALWAYS retrieve:

- card_id
- customer_name
- billing_month
- total_spend
- total_transactions
- category-wise spend breakdown
- top merchants
- international spend
- reward points earned
- month-over-month spend change percentage

The SQL query must return enough information to populate:

SpendSummaryResponse

Fields:

card_id
customer_name
billing_month
total_spend
total_transactions
category_breakdown
top_merchants
international_spend
reward_points_earned
mom_change_pct
Use the following context:

card_id = {card_id}

billing_month = {billing_month}

Return SQL only.

No markdown.
No explanation.

Database Schema:

{schema}
                """,
            ),
            (
                "human",
                """
Question:

{query}
                """,
            ),
        ]
    )

    chain = prompt | llm

    result = chain.invoke(
        {
            "query": query,
            "schema": schema,
            "card_id": card_id,
            "billing_month": billing_month,
        }
    )

    sql_query = clean_sql(result.content)
    print("\n===== GENERATED SQL =====\n")
    print(sql_query)

    validate_sql(sql_query)

    print("\n===== GENERATED SQL =====\n")
    print(sql_query)

    sql_result = db.run(sql_query)

    if not validate_sql_result(sql_result):

        raise ValueError("SQL returned no data.")

    sql_context = {
        "card_id": card_id,
        "billing_month": billing_month,
        "generated_sql": sql_query,
        "query_result": sql_result,
    }

    return {
        **state,
        "sql_context": sql_context,
    }
