from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.catalog import router as catalog_router
from app.api.routes.buyers import router as buyers_router
from app.api.routes.merchants import router as merchants_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.buyer_agent import router as buyer_agent_router
from app.api.routes.merchant_agent import router as merchant_agent_router
from app.api.routes.cart import router as cart_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0"
)

app.include_router(catalog_router)
app.include_router(buyers_router)
app.include_router(merchants_router)
app.include_router(recommendations_router)
app.include_router(buyer_agent_router)
app.include_router(merchant_agent_router)
app.include_router(cart_router)

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