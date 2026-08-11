def context_builder_node(state):

    sql_context = state.get("sql_context", {})

    docs = state.get("reranked_docs", [])

    kb_context = "\n\n".join([doc.page_content for doc in docs])

    final_context = f"""
SQL CONTEXT

{sql_context}


KNOWLEDGE BASE CONTEXT

{kb_context}
"""

    return {**state, "final_context": final_context}
