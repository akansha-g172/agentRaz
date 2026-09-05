from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db


router = APIRouter(
    prefix="/buyers",
    tags=["Buyers"]
)


@router.get("/demo")
def get_demo_buyer(
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            SELECT
                id,
                name,
                preferences,
                spending_limit
            FROM buyers
            ORDER BY created_at
            LIMIT 1;
        """)
    ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No buyer found"
        )

    return dict(result._mapping)