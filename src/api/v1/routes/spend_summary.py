from fastapi import APIRouter

from src.api.v1.schemas.query_schema import SpendSummaryRequest, SpendSummaryResponse

from src.api.v1.services.spend_summary_service import summarise_card_spend

router = APIRouter(prefix="/api/v1/summarise", tags=["Credit Card Spend Summary"])


@router.post("/")
def summarise_endpoint(request: SpendSummaryRequest) -> SpendSummaryResponse:

    response = summarise_card_spend(
        card_id=request.card_id,
        billing_month=request.billing_month,
    )

    return response
