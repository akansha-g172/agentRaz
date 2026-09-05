"""Order lifecycle — deterministic state machine."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.policies.policy_engine import evaluate_transaction
from app.services.audit_service import log_agent_action, log_audit
from app.services.cart_service import calculate_cart, validate_cart
from app.services.catalog_service import get_product


ORDER_STATUS = {
    "CREATED": "created",
    "PAYMENT_INITIATED": "payment_initiated",
    "PAID": "paid",
    "PAYMENT_FAILED": "payment_failed",
    "CANCELLED": "cancelled",
}


def _resolve_merchant_id(db: Session, items: list[dict]) -> str | None:
    for item in items:
        product = get_product(db, int(item["product_id"]))
        if product and product.get("merchant_id"):
            return str(product["merchant_id"])
    row = db.execute(
        text("SELECT id FROM merchants ORDER BY created_at LIMIT 1")
    ).fetchone()
    return str(row.id) if row else None


def _detect_upsell_items(db: Session, items: list[dict]) -> bool:
    """Treat non-primary categories (accessories) as upsell/cross-sell."""
    categories = set()
    for item in items:
        product = get_product(db, int(item["product_id"]))
        if product:
            categories.add((product.get("category") or "").lower())
    return len(categories) > 1 or any(
        c not in ("laptop", "monitor", "keyboard", "mouse", "headphones", "webcam", "storage")
        for c in categories
        if c
    )


def create_order(
    db: Session,
    *,
    items: list[dict],
    buyer_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    cart = calculate_cart(db, items)
    includes_upsell = _detect_upsell_items(db, items)
    merchant_id = _resolve_merchant_id(db, items)

    policy = evaluate_transaction(
        db,
        items=items,
        buyer_id=buyer_id,
        merchant_id=merchant_id,
        includes_upsell=includes_upsell,
    )

    if session_id:
        log_agent_action(
            db,
            session_id=session_id,
            agent_type="merchant",
            action="policy_check",
            arguments={"items": items, "includes_upsell": includes_upsell},
            result=policy,
        )
        log_audit(
            db,
            session_id=session_id,
            action="Create Order",
            reason=policy["reason"],
            amount=policy["requested_amount"],
            authorization_status=policy["authorization_status"],
            policy_result=policy["policy_result"],
        )

    if not policy["allowed"]:
        return {
            "success": False,
            "policy": policy,
            "order": None,
        }

    order_id = str(uuid4())
    db.execute(
        text("""
            INSERT INTO orders (
                id, buyer_id, merchant_id, total_amount, currency, status
            )
            VALUES (
                :id, :buyer_id, :merchant_id, :total_amount, :currency, :status
            )
        """),
        {
            "id": order_id,
            "buyer_id": policy.get("buyer_id"),
            "merchant_id": merchant_id,
            "total_amount": cart["subtotal"],
            "currency": cart["currency"],
            "status": ORDER_STATUS["CREATED"],
        },
    )

    for line in cart["items"]:
        db.execute(
            text("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (:order_id, :product_id, :quantity, :unit_price)
            """),
            {
                "order_id": order_id,
                "product_id": line["product_id"],
                "quantity": line["quantity"],
                "unit_price": line["unit_price"],
            },
        )

    db.commit()

    order = get_order(db, order_id)
    return {
        "success": True,
        "policy": policy,
        "order": order,
    }


def get_order(db: Session, order_id: str) -> dict | None:
    row = db.execute(
        text("""
            SELECT
                id, buyer_id, merchant_id, razorpay_order_id,
                total_amount, currency, status, created_at
            FROM orders
            WHERE id::text = :order_id
        """),
        {"order_id": order_id},
    ).fetchone()

    if not row:
        return None

    order = dict(row._mapping)
    order["total_amount"] = float(order["total_amount"])

    items = db.execute(
        text("""
            SELECT
                oi.product_id,
                oi.quantity,
                oi.unit_price,
                p.name,
                p.brand
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id::text = :order_id
        """),
        {"order_id": order_id},
    ).fetchall()

    order["items"] = [
        {
            **dict(item._mapping),
            "unit_price": float(item.unit_price),
            "line_total": float(item.unit_price) * item.quantity,
        }
        for item in items
    ]

    payments = db.execute(
        text("""
            SELECT id, razorpay_payment_id, status, method, amount, failure_reason, created_at
            FROM payments
            WHERE order_id::text = :order_id
            ORDER BY created_at
        """),
        {"order_id": order_id},
    ).fetchall()

    order["payments"] = [
        {
            **dict(p._mapping),
            "amount": float(p.amount) if p.amount is not None else None,
        }
        for p in payments
    ]

    return order


def update_order_status(db: Session, order_id: str, status: str) -> None:
    db.execute(
        text("""
            UPDATE orders SET status = :status
            WHERE id::text = :order_id
        """),
        {"order_id": order_id, "status": status},
    )
    db.commit()


def get_order_by_razorpay_id(db: Session, razorpay_order_id: str) -> dict | None:
    row = db.execute(
        text("""
            SELECT id FROM orders
            WHERE razorpay_order_id = :razorpay_order_id
        """),
        {"razorpay_order_id": razorpay_order_id},
    ).fetchone()
    if not row:
        return None
    return get_order(db, str(row.id))
