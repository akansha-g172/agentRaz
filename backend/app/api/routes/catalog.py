from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db


router = APIRouter(
    prefix="/catalog",
    tags=["Catalog"]
)


@router.get("/products")
def get_products(
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("""
            SELECT
                id,
                name,
                category,
                brand,
                price,
                specifications,
                use_cases
            FROM products
            WHERE active = TRUE
            ORDER BY id;
        """)
    )

    products = [
        dict(row._mapping)
        for row in result
    ]

    return {
        "count": len(products),
        "products": products
    }