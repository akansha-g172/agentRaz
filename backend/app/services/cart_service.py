"""Deterministic cart calculation — prices always from PostgreSQL."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.catalog_service import check_inventory, get_product


def calculate_cart(db: Session, items: list[dict]) -> dict:
    line_items = []
    subtotal = 0.0
    currency = "INR"

    for item in items:
        product_id = int(item["product_id"])
        quantity = int(item.get("quantity", 1))

        product = get_product(db, product_id)
        if not product:
            line_items.append({
                "product_id": product_id,
                "name": "Unknown product",
                "brand": None,
                "quantity": quantity,
                "unit_price": 0.0,
                "line_total": 0.0,
                "in_stock": False,
                "available_quantity": 0,
            })
            continue

        unit_price = float(product["price"])
        line_total = round(unit_price * quantity, 2)
        stock = int(product.get("stock_quantity") or 0)

        line_items.append({
            "product_id": product_id,
            "name": product["name"],
            "brand": product.get("brand"),
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
            "in_stock": stock >= quantity and product.get("active", True),
            "available_quantity": stock,
        })
        subtotal += line_total

    return {
        "items": line_items,
        "subtotal": round(subtotal, 2),
        "currency": currency,
    }


def validate_cart(db: Session, items: list[dict]) -> dict:
    cart = calculate_cart(db, items)
    errors: list[str] = []

    for line in cart["items"]:
        product_id = line["product_id"]
        quantity = line["quantity"]

        if line["name"] == "Unknown product":
            errors.append(f"Product {product_id} not found")
            continue

        inventory = check_inventory(db, product_id, quantity)
        if not inventory["available"]:
            errors.append(
                f"{line['name']}: {inventory['reason']}"
            )

    return {
        "valid": len(errors) == 0,
        "items": cart["items"],
        "subtotal": cart["subtotal"],
        "currency": cart["currency"],
        "errors": errors,
    }
