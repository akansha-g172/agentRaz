import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.buyer_agent import extract_buyer_intent


router = APIRouter(
    prefix="/buyer-agent",
    tags=["Buyer Agent"]
)


class BuyerMessage(BaseModel):
    message: str


@router.post("/intent")
def get_buyer_intent(request: BuyerMessage):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Buyer message cannot be empty"
        )

    try:
        intent = extract_buyer_intent(
            request.message
        )

        return {
            "message": request.message,
            "intent": intent
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Buyer agent failed: {str(e)}"
        )