# from fastapi import APIRouter

# from src.api.v1.schemas.query_schema import (
#     QueryRequest,
#     QueryResponse,
# )

# from src.api.v1.agents.credit_card_agent import (
#     run_credit_card_agent,
# )

# router = APIRouter(
#     prefix="/api/v1/query",
#     tags=["Query"],
# )


# @router.post(
#     "/",
#     response_model=QueryResponse,
# )
# def query_documents(request: QueryRequest):

#     return run_credit_card_agent(query=request.query)

from fastapi import (
    APIRouter,
    HTTPException,
)

from src.core.guardrails import (
    GuardrailViolation,
)

from src.api.v1.services.query_service import (
    query_documents,
)

from src.api.v1.schemas.query_schema import (
    QueryRequest,
    QueryResponse,
)

router = APIRouter(
    prefix="/api/v1/query",
    tags=["Credit Card Query"],
)


@router.post(
    "/",
    response_model=QueryResponse,
)
def query_endpoint(
    request: QueryRequest,
):

    try:

        return query_documents(request.query)

    except GuardrailViolation as violation:

        raise HTTPException(
            status_code=400,
            detail={
                "guardrail": violation.guard,
                "message": violation.message,
            },
        )
