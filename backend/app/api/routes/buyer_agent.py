from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.buyer_agent import extract_buyer_intent
from app.core.database import get_db
from app.services.recommendation_service import recommend_products


router = APIRouter(
    prefix="/buyer-agent",
    tags=["Buyer Agent"]
)


class BuyerMessage(BaseModel):
    message: str


def _intent_to_dict(intent) -> dict:
    """Normalize Gemini parsed intent into a plain dict."""
    if intent is None:
        return {}
    if isinstance(intent, dict):
        return intent
    if hasattr(intent, "model_dump"):
        return intent.model_dump()
    if hasattr(intent, "dict"):
        return intent.dict()
    return dict(intent)


@router.post("/intent")
def get_buyer_intent(request: BuyerMessage):
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Buyer message cannot be empty"
        )

    try:
        intent = extract_buyer_intent(request.message)
        return {
            "message": request.message,
            "intent": _intent_to_dict(intent),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Buyer agent failed: {str(e)}"
        )


@router.post("/search")
def search_products_for_buyer(
    request: BuyerMessage,
    db: Session = Depends(get_db),
    limit: int = 5,
):
    """
    Stage 6 flow:
      natural language → Buyer Agent intent → recommendation engine
      → hard constraint filtering → ranked recommendations
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Buyer message cannot be empty"
        )

    try:
        intent = _intent_to_dict(extract_buyer_intent(request.message))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Buyer agent failed: {str(e)}"
        )

    category = intent.get("category")
    max_price = intent.get("max_price")
    preferred_brands = intent.get("preferred_brands") or []
    use_case = intent.get("use_case")
    preferences = intent.get("preferences") or []

    # Coerce max_price if Gemini returns it as a string.
    if max_price is not None:
        try:
            max_price = float(max_price)
        except (TypeError, ValueError):
            max_price = None

    recommendations = recommend_products(
        db=db,
        category=category,
        max_price=max_price,
        preferred_brands=preferred_brands,
        use_case=use_case,
        preferences=preferences,
        limit=limit,
    )

    return {
        "query": request.message,
        "intent": intent,
        "recommendations": recommendations,
    }
