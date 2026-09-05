from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.service import (
    get_aov,
    get_conversion,
    get_revenue,
    get_summary,
    get_uplift,
    get_upsell_metrics,
)
from app.core.database import get_db


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/revenue")
def revenue(db: Session = Depends(get_db)):
    return get_revenue(db)


@router.get("/conversion")
def conversion(db: Session = Depends(get_db)):
    return get_conversion(db)


@router.get("/aov")
def aov(db: Session = Depends(get_db)):
    return get_aov(db)


@router.get("/upsell")
def upsell(db: Session = Depends(get_db)):
    return get_upsell_metrics(db)


@router.get("/uplift")
def uplift(db: Session = Depends(get_db)):
    return get_uplift(db)


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return get_summary(db)
