# from src.api.v1.agents.agents import run_credit_card_agent_stream

from src.api.v1.schemas.query_schema import QueryRequest
from src.api.v1.agents.credit_card_agent import run_credit_card_agent


def query_documents(request: QueryRequest):
    return run_credit_card_agent(request.query)
