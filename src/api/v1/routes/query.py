from fastapi import APIRouter

from src.api.v1.schemas.query_schema import (
    QueryRequest,
    QueryResponse,
)

from src.api.v1.agents.credit_card_agent import (
    run_credit_card_agent,
)

router = APIRouter(
    prefix="/api/v1/query",
    tags=["Query"],
)


@router.post(
    "/",
    response_model=QueryResponse,
)
def query_documents(request: QueryRequest):

    return run_credit_card_agent(query=request.query)
