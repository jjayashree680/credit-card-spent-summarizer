from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from pydantic import BaseModel
from typing import List

# ==========================
# REQUEST MODELS
# ==========================


class QueryRequest(BaseModel):
    query: str


class SpendSummaryRequest(BaseModel):
    card_id: str
    billing_month: str


class CategoryBreakdown(BaseModel):

    category: str

    txn_count: int

    amount: float


class TopMerchant(BaseModel):

    merchant_name: str

    amount: float


# ==========================
# INTENT NODE
# ==========================


class IntentDecision(BaseModel):

    need_sql: bool = Field(description="Whether SQL retrieval is required")

    need_rag: bool = Field(description="Whether RAG retrieval is required")

    reason: str = Field(description="Reason for intent classification")


# ==========================
# SQL NODE
# ==========================


class SQLResponse(BaseModel):

    generated_sql: str

    query_result: str


# ==========================
# QUERY API RESPONSE
# ==========================


class QueryResponse(BaseModel):

    query: str

    answer: str

    policy_citations: str

    page_no: str

    document_name: str

    sql_query_executed: Optional[str] = None


# ==========================
# SUMMARISE API RESPONSE
# ==========================


# class SpendSummaryResponse(BaseModel):

#     card_id: str

#     customer_name: str

#     billing_month: str

#     total_spend: float

#     total_transactions: int

#     category_breakdown: List[Dict[str, Any]]

#     top_merchants: List[Dict[str, Any]]

#     international_spend: float

#     reward_points_earned: int

#     mom_change_pct: float

#     summary_text: str

#     tip: str


class SpendSummaryResponse(BaseModel):

    card_id: str

    customer_name: str

    billing_month: str

    total_spend: float

    total_transactions: int

    category_breakdown: List[CategoryBreakdown]

    top_merchants: List[TopMerchant]

    international_spend: float

    reward_points_earned: int

    mom_change_pct: float

    summary_text: str

    tip: str


# ==========================
# LLM NARRATIVE MODEL
# ==========================


class SpendNarrative(BaseModel):

    summary_text: str

    tip: str


# ==========================
# EVALUATION
# ==========================


class EvaluationResult(BaseModel):

    passed: bool

    reason: str


# ==========================
# RESPONSE GUARDRAILS
# ==========================


class GuardrailResult(BaseModel):

    passed: bool

    reason: str