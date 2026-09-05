from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.recommendation_service import recommend_products


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/products")
def get_recommendations(
    category: str | None = None,
    max_price: float | None = None,
    brand: str | None = None,
    use_case: str | None = None,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    preferred_brands = []

    if brand:
        preferred_brands = [
            value.strip()
            for value in brand.split(",")
        ]

    products = recommend_products(
        db=db,
        category=category,
        max_price=max_price,
        preferred_brands=preferred_brands,
        use_case=use_case,
        limit=limit,
    )

    return {
        "count": len(products),
        "recommendations": products
    }