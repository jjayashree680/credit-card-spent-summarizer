from pydantic import BaseModel, Field
from typing import Optional, List

# ==========================
# Query API
# ==========================


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    policy_citations: str
    page_no: str
    document_name: str
    sql_query_executed: Optional[str]


class AIResponse(BaseModel):
    query: str = Field(description="The given query by user")
    answer: str = Field(description="The generated response")
    policy_citations: str
    page_no: str
    document_name: str
    sql_query_executed: Optional[str]


# ==========================
# Spend Summary API
# ==========================


class SpendSummaryRequest(BaseModel):
    card_id: str
    billing_month: str


class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    txn_count: int
    pct_of_total: float


class Merchant(BaseModel):
    merchant_name: str
    amount: float


class InternationalSpend(BaseModel):
    amount: float
    txn_count: int


class RewardSummary(BaseModel):
    points_earned: int
    redemption_value: float


class SpendSummaryResponse(BaseModel):
    card_id: str
    customer_name: str
    billing_month: str

    total_spend: float
    total_transactions: int

    category_breakdown: List[CategoryBreakdown]
    top_merchants: List[Merchant]

    international_spend: InternationalSpend

    reward_summary: RewardSummary

    mom_change_pct: float

    summary_text: str

    tip: str
