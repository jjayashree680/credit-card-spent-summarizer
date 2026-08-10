from src.core.db import get_sql_database


def sql_retrieval_node(state):

    print("===== SQL RETRIEVAL =====")

    db = get_sql_database()

    schema = db.get_table_info()

    sql_context = {"schema": schema}

    return {**state, "sql_context": sql_context}
