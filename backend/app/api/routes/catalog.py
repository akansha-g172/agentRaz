from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.catalog_service import get_product, search_products


router = APIRouter(
    prefix="/catalog",
    tags=["Catalog"],
)


@router.get("/products")
def get_products(
    db: Session = Depends(get_db),
):
    products = search_products(db, limit=100)
    return {
        "count": len(products),
        "products": products,
    }


@router.get("/products/{product_id}")
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/search")
def search_catalog(
    category: str | None = None,
    brand: str | None = None,
    max_price: float | None = None,
    q: str | None = Query(default=None, description="Free-text search"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    products = search_products(
        db,
        category=category,
        brand=brand,
        max_price=max_price,
        query=q,
        limit=limit,
    )
    return {
        "count": len(products),
        "products": products,
    }
