# from src.core.db import get_vector_store

# vector_store = get_vector_store()

# docs = vector_store.similarity_search("forex markup", k=5)

# print(len(docs))

# for doc in docs:
#     print(doc.page_content[:200])


# from src.api.v1.tools.hybrid_search_tool import hybrid_search_node

# state = {"query": "forex markup"}

# result = hybrid_search_node(state)

# print("Vector:", len(result["vector_docs"]))

# print("FTS:", len(result["fts_docs"]))

# print("Hybrid:", len(result["hybrid_docs"]))


# from dotenv import load_dotenv
# from sqlalchemy import create_engine, text
# import os

# load_dotenv()

# engine = create_engine(os.getenv("PG_CONNECTION_STRING"))

# with engine.connect() as conn:

#     result = conn.execute(text("""
#         SELECT column_name
#         FROM information_schema.columns
#         WHERE table_name='langchain_pg_embedding';
#         """))

#     for row in result:
#         print(row)

# from src.core.db import get_sql_database

# db = get_sql_database()

# print(db.get_table_info())

# from sqlalchemy import create_engine, inspect
# import os

# from dotenv import load_dotenv

# load_dotenv()

# connection = os.getenv("PG_RDBMS_CONNECTION_STRING")

# engine = create_engine(connection)

# inspector = inspect(engine)

# tables = inspector.get_table_names()

# print("\n===== DATABASE TABLES =====")

# for table in tables:
#     print(table)


# from src.core.db import get_sql_database

# db = get_sql_database()

# print(db.get_table_info())

# # src / retrieval / test_nl2sql.py

# from src.api.v1.tools.sql_retrieval_tool import sql_retrieval_node

# state = {
#     "query": "Summarise my spending by category for March 2026 on CC-881001",
#     "card_id": "CC-881001",
#     "billing_month": "2026-03",
# }

# result = sql_retrieval_node(state)

# print(result["sql_context"])

# src/retrieval/test_agent.py

from src.api.v1.agents.credit_card_agent import run_credit_card_agent

response = run_credit_card_agent(
    query="""
    Summarise my spending by category
    for March 2026 on CC-881001
    """,
    card_id="CC-881001",
    billing_month="2026-03",
)

print(response)


# from dotenv import load_dotenv
# import os

# load_dotenv()

# print(os.getenv("PG_RDBMS_CONNECTION_STRING"))
