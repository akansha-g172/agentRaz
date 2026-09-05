from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.commerce import (
    CartCalculateRequest,
    CartCalculateResponse,
    CartValidationResult,
)
from app.services.cart_service import calculate_cart, validate_cart


router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)


@router.post("/calculate", response_model=CartCalculateResponse)
def calculate_cart_endpoint(
    request: CartCalculateRequest,
    db: Session = Depends(get_db),
):
    if not request.items:
        raise HTTPException(status_code=400, detail="Cart must contain at least one item")

    items = [item.model_dump() for item in request.items]
    return calculate_cart(db, items)


@router.post("/validate", response_model=CartValidationResult)
def validate_cart_endpoint(
    request: CartCalculateRequest,
    db: Session = Depends(get_db),
):
    if not request.items:
        raise HTTPException(status_code=400, detail="Cart must contain at least one item")

    items = [item.model_dump() for item in request.items]
    return validate_cart(db, items)
