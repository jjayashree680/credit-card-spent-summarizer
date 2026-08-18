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

def get_person_not_found_response(query: str):
    return {
        "query": query,
        "answer": "I couldn't find a credit card matching that person.",
        "policy_citations": "",
        "page_no": "",
        "document_name": "",
        "sql_query_executed": None,
    }

def sql_retrieval_node(state):

    print("===== NL2SQL NODE =====")
    role = state.get("role", "guest")
    username = state.get("username")

    query = state["query"]

    card_id = state.get("card_id")

    billing_month = state.get("billing_month")
    effective_query = query

    if card_id:
        effective_query += f"\nUse card_id={card_id}"

    if billing_month:
        effective_query += f"\nUse billing_month={billing_month}"

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
Resolved Context

card_id = {card_id}

billing_month = {billing_month}

CRITICAL RULES

1. If card_id is provided, ALWAYS filter on that card_id.
2. If billing_month is provided, ALWAYS use that billing_month.
3. Do NOT replace billing_month with CURRENT_DATE calculations.
4. Do NOT infer another month when billing_month is available.
5. Follow-up questions such as:
   - "last month"
   - "this month"
   - "highest spend category"
   - "top merchant"
   must use the provided card_id and billing_month.
6. CURRENT_DATE may be used ONLY when billing_month is NULL.

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

Resolved Card ID:
{card_id}

Resolved Billing Month:
{billing_month}
    """,
            ),
        ]
    )

    chain = prompt | llm
    print("NL2SQL CARD ID =", card_id)
    print("NL2SQL BILLING MONTH =", billing_month)
    print("EFFECTIVE QUERY =")
    print(effective_query)

    result = chain.invoke(
        {
            "query": effective_query,
            "schema": schema,
            "card_id": card_id,
            "billing_month": billing_month,
        }
    )

    sql_query = clean_sql(result.content)
    print("\n===== GENERATED SQL =====\n")
    print(sql_query)

    validate_sql(sql_query)
    sql_result = db.run(sql_query)

    if not validate_sql_result(sql_result):

        print("===== SQL RETURNED NO DATA =====")

        return {
            **state,
            "sql_context": {
                "card_id": card_id,
                "billing_month": billing_month,
                "generated_sql": sql_query,
                "query_result": [],
            },
            "response": get_person_not_found_response(query),
        }

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
