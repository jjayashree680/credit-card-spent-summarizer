from src.api.v1.agents.credit_card_agent import (
    credit_card_graph,
)

from src.api.v1.agents.spend_summary_agent import (
    build_spend_summary,
)


def summarise_card_spend(
    card_id: str,
    billing_month: str,
):

    print("STEP 1 - Entered summarise_card_spend")

    initial_state = {
        "query": (
            f"Summarise the credit card spending "
            f"for card {card_id} "
            f"for billing month {billing_month}"
        ),
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

    print("STEP 2 - Before graph invoke")

    final_state = credit_card_graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": f"{card_id}_{billing_month}"}},
    )

    print("STEP 3 - After graph invoke")

    response = build_spend_summary(final_state)

    print("STEP 4 - After build_spend_summary")

    return response
