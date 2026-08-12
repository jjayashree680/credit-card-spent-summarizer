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
                You are a PostgreSQL expert.

                Use ONLY these tables:

                customers
                credit_cards
                card_transactions
                reward_transactions
                billing_statements

                Generate ONLY SELECT statements.

                Context:

                card_id = {card_id}
                billing_month = {billing_month}

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

    sql_query = result.content.replace("```sql", "").replace("```", "").strip()

    sql_result = db.run(sql_query)

    sql_context = {"generated_sql": sql_query, "query_result": sql_result}

    return {**state, "sql_context": sql_context}
