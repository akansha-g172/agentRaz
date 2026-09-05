from sqlalchemy import text
from sqlalchemy.orm import Session


def recommend_products(
    db: Session,
    category: str | None = None,
    max_price: float | None = None,
    preferred_brands: list[str] | None = None,
    use_case: str | None = None,
    limit: int = 5
):
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

    params = {}

    if category:
        query += """
            AND LOWER(p.category) = LOWER(:category)
        """
        params["category"] = category

    if max_price is not None:
        query += """
            AND p.price <= :max_price
        """
        params["max_price"] = max_price

    query += """
        ORDER BY p.price ASC
    """

    result = db.execute(
        text(query),
        params
    ).fetchall()

    products = []

    preferred_brands = preferred_brands or []

    for row in result:
        product = dict(row._mapping)

        score = 0
        reasons = []

        # Brand preference
        if product["brand"] in preferred_brands:
            score += 30
            reasons.append("preferred brand")

        # Use-case matching
        if use_case:
            product_use_cases = [
                value.lower()
                for value in (product["use_cases"] or [])
            ]

            if use_case.lower() in product_use_cases:
                score += 40
                reasons.append(f"matches use case: {use_case}")

        # Lower price gets a small advantage
        if max_price and product["price"] <= max_price:
            price_ratio = product["price"] / max_price

            if price_ratio <= 0.8:
                score += 15
                reasons.append("well within budget")
            else:
                score += 5

        product["recommendation_score"] = score
        product["recommendation_reasons"] = reasons

        products.append(product)

    # Highest score first
    products.sort(
        key=lambda product: (
            -product["recommendation_score"],
            product["price"]
        )
    )

    return products[:limit]