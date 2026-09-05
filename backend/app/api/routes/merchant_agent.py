from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.merchant_agent import handle_commerce_request
from app.core.database import get_db
from app.schemas.commerce import CommerceRequest


router = APIRouter(
    prefix="/merchant-agent",
    tags=["Merchant Agent"],
)


class MerchantChatRequest(BaseModel):
    commerce_request: CommerceRequest


@router.post("/offer")
def create_commerce_offer(
    request: CommerceRequest,
    db: Session = Depends(get_db),
):
    """
    Structured agentic commerce protocol:
      commerce_request → merchant agent → commerce_offer
    """
    try:
        return handle_commerce_request(db, request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Merchant agent failed: {str(e)}",
        )


@router.post("/chat")
def merchant_chat(
    body: MerchantChatRequest,
    db: Session = Depends(get_db),
):
    """Alias for structured merchant commerce handling."""
    return create_commerce_offer(body.commerce_request, db)
