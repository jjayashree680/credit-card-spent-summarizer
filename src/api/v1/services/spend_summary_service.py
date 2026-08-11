from src.api.v1.agents.credit_card_agent import run_credit_card_agent


def summarise_card_spend(
    card_id: str,
    billing_month: str,
):
    query = (
        f"Summarise the credit card spending "
        f"for card {card_id} "
        f"for billing month {billing_month}."
    )

    return run_credit_card_agent(
        query=query,
        card_id=card_id,
        billing_month=billing_month,
        thread_id=f"{card_id}-{billing_month}",
    )