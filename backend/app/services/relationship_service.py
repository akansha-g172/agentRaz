"""Deterministic upsell / cross-sell from product_relationships table."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_related_products(
    db: Session,
    product_id: int,
    relationship_types: list[str] | None = None,
    limit: int = 5,
) -> list[dict]:
    types = relationship_types or [
        "frequently_bought",
        "compatible_with",
        "upsell",
        "cross_sell",
    ]

    rows = db.execute(
        text("""
            SELECT
                pr.relationship_type,
                pr.confidence,
                p.id,
                p.name,
                p.brand,
                p.price,
                p.category,
                i.stock_quantity
            FROM product_relationships pr
            JOIN products p ON pr.related_product_id = p.id
            JOIN inventory i ON p.id = i.product_id
            WHERE pr.product_id = :product_id
              AND pr.relationship_type = ANY(:types)
              AND p.active = TRUE
              AND i.stock_quantity > 0
            ORDER BY pr.confidence DESC NULLS LAST, p.price ASC
            LIMIT :limit
        """),
        {
            "product_id": product_id,
            "types": types,
            "limit": limit,
        },
    ).fetchall()

    related = []
    for row in rows:
        item = dict(row._mapping)
        item["price"] = float(item["price"])
        item["confidence"] = (
            float(item["confidence"]) if item["confidence"] is not None else None
        )
        item["stock_quantity"] = int(item["stock_quantity"] or 0)
        related.append(item)
    return related
