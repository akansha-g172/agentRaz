from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.commerce import CreateOrderRequest, InitiatePaymentRequest
from app.services.audit_service import create_session, log_agent_action
from app.services.order_service import create_order, get_order
from app.razorpay.service import create_razorpay_order


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.post("/")
def create_order_endpoint(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
):
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    session_id = request.session_id
    if not session_id:
        session_id = create_session(db, buyer_id=request.buyer_id)

    items = [item.model_dump() for item in request.items]

    log_agent_action(
        db,
        session_id=session_id,
        agent_type="merchant",
        action="create_order_request",
        arguments={"items": items, "buyer_id": request.buyer_id},
    )

    result = create_order(
        db,
        items=items,
        buyer_id=request.buyer_id,
        session_id=session_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=403,
            detail={
                "message": result["policy"]["reason"],
                "policy": result["policy"],
            },
        )

    return {
        "session_id": session_id,
        "policy": result["policy"],
        "order": result["order"],
    }


@router.get("/{order_id}")
def get_order_endpoint(
    order_id: str,
    db: Session = Depends(get_db),
):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/{order_id}/pay")
def initiate_payment_endpoint(
    order_id: str,
    request: InitiatePaymentRequest | None = None,
    db: Session = Depends(get_db),
):
    session_id = request.session_id if request else None
    result = create_razorpay_order(db, order_id, session_id=session_id)

    if not result.get("success"):
        status = 403 if result.get("policy") and not result["policy"].get("allowed") else 400
        raise HTTPException(status_code=status, detail=result)

    return result
