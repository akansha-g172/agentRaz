from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.razorpay.service import handle_webhook


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str | None = Header(default=None),
    x_razorpay_event_id: str | None = Header(default=None),
):
    body = await request.body()

    result = handle_webhook(
        db,
        body=body,
        signature=x_razorpay_signature,
        event_id=x_razorpay_event_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)

    return result
