from src.api.v1.agents.agents import run_spend_summary_agent


def summarise_card_spend(card_id: str, billing_month: str):
    return run_spend_summary_agent(card_id=card_id, billing_month=billing_month)
