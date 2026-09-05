"""Controlled catalog tools — backend functions agents may request."""

from sqlalchemy.orm import Session

from app.services.catalog_service import check_inventory, get_product, search_products
from app.services.recommendation_service import recommend_products
from app.services.relationship_service import get_related_products


def search_catalog(
    db: Session,
    *,
    category: str | None = None,
    brand: str | None = None,
    max_price: float | None = None,
    query: str | None = None,
    limit: int = 20,
) -> dict:
    products = search_products(
        db,
        category=category,
        brand=brand,
        max_price=max_price,
        query=query,
        limit=limit,
    )
    return {"count": len(products), "products": products}


def get_product_details(db: Session, product_id: int) -> dict:
    product = get_product(db, product_id)
    if not product:
        return {"found": False, "product": None}
    return {"found": True, "product": product}


def check_product_inventory(
    db: Session,
    product_id: int,
    quantity: int = 1,
) -> dict:
    return check_inventory(db, product_id, quantity)


def get_recommendations(
    db: Session,
    *,
    category: str | None = None,
    max_price: float | None = None,
    preferred_brands: list[str] | None = None,
    use_case: str | None = None,
    preferences: list[str] | None = None,
    limit: int = 5,
) -> dict:
    recommendations = recommend_products(
        db=db,
        category=category,
        max_price=max_price,
        preferred_brands=preferred_brands,
        use_case=use_case,
        preferences=preferences,
        limit=limit,
    )
    return {"count": len(recommendations), "recommendations": recommendations}


def get_product_addons(
    db: Session,
    product_id: int,
    limit: int = 5,
) -> dict:
    addons = get_related_products(db, product_id, limit=limit)
    return {"count": len(addons), "addons": addons}
