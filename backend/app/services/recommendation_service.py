"""Deterministic product recommendation engine.

Hard constraints (budget, stock, active) are enforced in SQL / Python —
never by the LLM. Soft signals only affect ranking score.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


# Scoring weights — keep understandable and configurable for the MVP.
WEIGHTS = {
    "budget_fit": 20,
    "use_case_match": 30,
    "brand_match": 25,
    "specification_match": 15,
    "portability_match": 10,
    "inventory_score": 10,
}


def recommend_products(
    db: Session,
    category: str | None = None,
    max_price: float | None = None,
    preferred_brands: list[str] | None = None,
    use_case: str | None = None,
    preferences: list[str] | None = None,
    limit: int = 5,
) -> list[dict]:
    """Search products, apply hard filters, rank, and return recommendations."""

    query = """
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
        JOIN inventory i
            ON p.id = i.product_id
        WHERE p.active = TRUE
          AND i.stock_quantity > 0
    """

    params: dict = {}

    if category:
        # Soft category match: equality after lowercasing (seed uses "Laptop").
        query += """
            AND LOWER(p.category) = LOWER(:category)
        """
        params["category"] = category.strip()

    # HARD CONSTRAINT: never recommend above the buyer's max budget.
    if max_price is not None:
        query += """
            AND p.price <= :max_price
        """
        params["max_price"] = max_price

    result = db.execute(text(query), params).fetchall()

    preferred_brands = preferred_brands or []
    preferences = preferences or []
    preferred_brands_lower = [b.lower() for b in preferred_brands if b]
    preferences_lower = [p.lower() for p in preferences if p]

    products: list[dict] = []

    for row in result:
        raw = dict(row._mapping)
        price = float(raw["price"])

        # Defense-in-depth: hard budget filter again in Python.
        if max_price is not None and price > max_price:
            continue

        scored = _score_product(
            product=raw,
            price=price,
            max_price=max_price,
            preferred_brands_lower=preferred_brands_lower,
            use_case=use_case,
            preferences_lower=preferences_lower,
        )
        products.append(scored)

    products.sort(
        key=lambda product: (
            -product["recommendation_score"],
            product["price"],
        )
    )

    return products[:limit]


def _score_product(
    product: dict,
    price: float,
    max_price: float | None,
    preferred_brands_lower: list[str],
    use_case: str | None,
    preferences_lower: list[str],
) -> dict:
    score = 0
    reasons: list[str] = []

    specs = product.get("specifications") or {}
    if not isinstance(specs, dict):
        specs = {}

    # --- budget_fit ---
    if max_price is not None:
        price_ratio = price / max_price if max_price > 0 else 1.0
        if price_ratio <= 0.8:
            score += WEIGHTS["budget_fit"]
            reasons.append(f"Well within your ₹{int(max_price):,} budget")
        else:
            # Still within hard budget (already filtered); smaller boost.
            score += max(5, int(WEIGHTS["budget_fit"] * 0.4))
            reasons.append(f"Within your ₹{int(max_price):,} budget")

    # --- use_case_match ---
    if use_case:
        product_use_cases = [
            value.lower() for value in (product.get("use_cases") or [])
        ]
        use_case_lower = use_case.lower()
        if use_case_lower in product_use_cases or any(
            use_case_lower in uc or uc in use_case_lower for uc in product_use_cases
        ):
            score += WEIGHTS["use_case_match"]
            reasons.append(f"Suitable for {use_case}")

    # --- brand_match ---
    brand = (product.get("brand") or "")
    if brand and brand.lower() in preferred_brands_lower:
        score += WEIGHTS["brand_match"]
        reasons.append(f"Matches preferred brand: {brand}")

    # --- specification_match (RAM / storage when present) ---
    ram = specs.get("ram")
    storage = specs.get("storage")
    if ram:
        score += WEIGHTS["specification_match"] // 2
        reasons.append(str(ram) if "RAM" in str(ram).upper() or "GB" in str(ram).upper() else f"{ram} RAM")
    if storage:
        score += WEIGHTS["specification_match"] // 2
        reasons.append(str(storage))

    # --- portability_match ---
    wants_portable = any(
        token in preferences_lower
        for token in ("lightweight", "portable", "light", "travel")
    )
    if wants_portable:
        weight_str = str(specs.get("weight") or "")
        weight_kg = _parse_weight_kg(weight_str)
        if weight_kg is not None and weight_kg <= 1.5:
            score += WEIGHTS["portability_match"]
            reasons.append(f"Portable ({weight_str})")
        elif "lightweight" in (product.get("description") or "").lower():
            score += WEIGHTS["portability_match"] // 2
            reasons.append("Described as lightweight")

    # --- inventory_score ---
    stock = int(product.get("stock_quantity") or 0)
    if stock >= 20:
        score += WEIGHTS["inventory_score"]
        reasons.append("In stock")
    elif stock > 0:
        score += WEIGHTS["inventory_score"] // 2
        reasons.append("Limited stock")

    return {
        "product_id": product["id"],
        "name": product["name"],
        "brand": product.get("brand"),
        "category": product.get("category"),
        "description": product.get("description"),
        "price": price,
        "specifications": specs,
        "use_cases": product.get("use_cases") or [],
        "stock_quantity": stock,
        "recommendation_score": score,
        "reasons": reasons,
    }


def _parse_weight_kg(weight_str: str) -> float | None:
    """Parse values like '1.45 kg' into a float kilograms value."""
    if not weight_str:
        return None
    cleaned = weight_str.lower().replace("kg", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None
