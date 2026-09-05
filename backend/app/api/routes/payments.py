from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.commerce import PolicyCheckRequest, VerifyPaymentRequest
from app.policies.policy_engine import evaluate_transaction
from app.razorpay.service import get_payment, verify_payment


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post("/verify")
def verify_payment_endpoint(
    request: VerifyPaymentRequest,
    db: Session = Depends(get_db),
):
    result = verify_payment(
        db,
        razorpay_order_id=request.razorpay_order_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_signature=request.razorpay_signature,
        session_id=request.session_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/{payment_id}")
def get_payment_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
):
    payment = get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


policy_router = APIRouter(
    prefix="/policy",
    tags=["Policy"],
)


@policy_router.post("/check")
def policy_check_endpoint(
    request: PolicyCheckRequest,
    db: Session = Depends(get_db),
):
    items = [item.model_dump() for item in request.items]
    return evaluate_transaction(
        db,
        items=items,
        buyer_id=request.buyer_id,
        merchant_id=request.merchant_id,
        includes_upsell=request.includes_upsell,
    )
