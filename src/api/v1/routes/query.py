from fastapi import APIRouter

from src.api.v1.schemas.query_schema import QueryRequest, QueryResponse
from src.api.v1.services.query_service import query_documents
from src.api.v1.agents.credit_card_agent import run_credit_card_agent

router = APIRouter(
    prefix="/api/v1/query",
    tags=["Query"],
)


@router.post("/")
def query_documents(request: QueryRequest):
    return run_credit_card_agent(request.query)
