from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db


router = APIRouter(
    prefix="/merchants",
    tags=["Merchants"]
)


@router.get("/demo")
def get_demo_merchant(
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            SELECT
                id,
                name,
                description
            FROM merchants
            ORDER BY created_at
            LIMIT 1;
        """)
    ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No merchant found"
        )

    return dict(result._mapping)


@router.get("/demo/policy")
def get_demo_merchant_policy(
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            SELECT
                merchant_id,
                max_transaction_amount,
                max_discount_percent,
                max_retry_attempts,
                allow_upsell,
                require_confirmation_above
            FROM merchant_policies
            ORDER BY created_at
            LIMIT 1;
        """)
    ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No merchant policy found"
        )

    return dict(result._mapping)