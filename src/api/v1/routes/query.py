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
from fastapi.responses import StreamingResponse

from src.core.guardrails import (
    GuardrailViolation,
)

from src.api.v1.services.query_service import (
    query_documents,
    query_documents_stream,
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

        return query_documents(
            query=request.query,
            thread_id=request.thread_id,
            chat_history=request.chat_history,
            role=request.role,
            username=request.username,
        )

    except GuardrailViolation as violation:

        raise HTTPException(
            status_code=400,
            detail={
                "guardrail": violation.guard,
                "message": violation.message,
            },
        )


@router.post("/stream")
def stream_query(
    request: QueryRequest,
):

    return StreamingResponse(
        query_documents_stream(
            query=request.query,
            thread_id=request.thread_id,
            chat_history=request.chat_history,
        ),
        media_type="text/plain",
    )
