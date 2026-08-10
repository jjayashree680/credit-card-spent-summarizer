from fastapi import FastAPI

from src.api.v1.routes.query import router as query_router
from src.api.v1.routes.spend_summary import router as spend_summary_router

app = FastAPI(title="Credit Card Spend Summarizer")

app.include_router(query_router)
app.include_router(spend_summary_router)
