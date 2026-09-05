from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.catalog import router as catalog_router
from app.api.routes.buyers import router as buyers_router
from app.api.routes.merchants import router as merchants_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.buyer_agent import router as buyer_agent_router
from app.api.routes.merchant_agent import router as merchant_agent_router
from app.api.routes.cart import router as cart_router
from app.api.routes.orders import router as orders_router
from app.api.routes.payments import router as payments_router, policy_router
from app.api.routes.webhooks import router as webhooks_router
from app.api.routes.audit import router as audit_router
from app.api.routes.analytics import router as analytics_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router)
app.include_router(buyers_router)
app.include_router(merchants_router)
app.include_router(recommendations_router)
app.include_router(buyer_agent_router)
app.include_router(merchant_agent_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(policy_router)
app.include_router(webhooks_router)
app.include_router(audit_router)
app.include_router(analytics_router)

@app.get("/")
def root():
    return {
        "message": "AgentPay API is running",
        "environment": settings.environment
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }