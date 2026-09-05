"""Deterministic catalog access — source of truth is PostgreSQL."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_product(db: Session, product_id: int) -> dict | None:
    row = db.execute(
        text("""
            SELECT
                p.id,
                p.merchant_id,
                p.name,
                p.category,
                p.brand,
                p.description,
                p.price,
                p.specifications,
                p.use_cases,
                p.active,
                i.stock_quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.id = :product_id
        """),
        {"product_id": product_id},
    ).fetchone()

    if not row:
        return None

    product = dict(row._mapping)
    product["price"] = float(product["price"])
    product["stock_quantity"] = int(product["stock_quantity"] or 0)
    return product


def search_products(
    db: Session,
    *,
    category: str | None = None,
    brand: str | None = None,
    max_price: float | None = None,
    query: str | None = None,
    limit: int = 20,
) -> list[dict]:
    sql = """
        SELECT
            p.id,
            p.name,
            p.category,
            p.brand,
            p.description,
            p.price,
            p.specifications,
            p.use_cases,
            i.stock_quantity
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE p.active = TRUE
          AND i.stock_quantity > 0
    """
    params: dict = {}

    if category:
        sql += " AND LOWER(p.category) = LOWER(:category)"
        params["category"] = category.strip()

    if brand:
        sql += " AND LOWER(p.brand) = LOWER(:brand)"
        params["brand"] = brand.strip()

    if max_price is not None:
        sql += " AND p.price <= :max_price"
        params["max_price"] = max_price

    if query:
        sql += """
            AND (
                LOWER(p.name) LIKE LOWER(:query)
                OR LOWER(p.description) LIKE LOWER(:query)
                OR LOWER(p.brand) LIKE LOWER(:query)
            )
        """
        params["query"] = f"%{query.strip()}%"

    sql += " ORDER BY p.price ASC LIMIT :limit"
    params["limit"] = limit

    rows = db.execute(text(sql), params).fetchall()
    products = []
    for row in rows:
        product = dict(row._mapping)
        product["price"] = float(product["price"])
        product["stock_quantity"] = int(product["stock_quantity"] or 0)
        products.append(product)
    return products


def check_inventory(db: Session, product_id: int, quantity: int = 1) -> dict:
    row = db.execute(
        text("""
            SELECT
                p.id,
                p.name,
                p.active,
                i.stock_quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.id = :product_id
        """),
        {"product_id": product_id},
    ).fetchone()

    if not row:
        return {
            "product_id": product_id,
            "available": False,
            "stock_quantity": 0,
            "requested_quantity": quantity,
            "reason": "Product not found",
        }

    data = dict(row._mapping)
    stock = int(data["stock_quantity"] or 0)
    active = bool(data["active"])

    if not active:
        return {
            "product_id": product_id,
            "name": data["name"],
            "available": False,
            "stock_quantity": stock,
            "requested_quantity": quantity,
            "reason": "Product is inactive",
        }

    if stock <= 0:
        return {
            "product_id": product_id,
            "name": data["name"],
            "available": False,
            "stock_quantity": stock,
            "requested_quantity": quantity,
            "reason": "Out of stock",
        }

    if stock < quantity:
        return {
            "product_id": product_id,
            "name": data["name"],
            "available": False,
            "stock_quantity": stock,
            "requested_quantity": quantity,
            "reason": f"Insufficient stock (available: {stock})",
        }

    return {
        "product_id": product_id,
        "name": data["name"],
        "available": True,
        "stock_quantity": stock,
        "requested_quantity": quantity,
        "reason": None,
    }
