# from src.core.db import get_vector_store

# vector_store = get_vector_store()

# docs = vector_store.similarity_search("forex markup", k=5)

# print(len(docs))

# for doc in docs:
#     print(doc.page_content[:200])


from src.api.v1.tools.hybrid_search_tool import hybrid_search_node

state = {"query": "forex markup"}

result = hybrid_search_node(state)

print("Vector:", len(result["vector_docs"]))

print("FTS:", len(result["fts_docs"]))

print("Hybrid:", len(result["hybrid_docs"]))


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
