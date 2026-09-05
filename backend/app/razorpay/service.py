"""Razorpay Test Mode integration — LLM never calls this directly."""

from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.policies.policy_engine import evaluate_transaction
from app.razorpay.client import get_razorpay_client, is_razorpay_configured
from app.services.audit_service import log_audit
from app.services.order_service import (
    ORDER_STATUS,
    get_order,
    get_order_by_razorpay_id,
    update_order_status,
)
from app.core.config import settings


def _order_items_as_dict(db: Session, order_id: str) -> list[dict]:
    rows = db.execute(
        text("""
            SELECT product_id, quantity
            FROM order_items
            WHERE order_id::text = :order_id
        """),
        {"order_id": order_id},
    ).fetchall()
    return [{"product_id": r.product_id, "quantity": r.quantity} for r in rows]


def create_razorpay_order(
    db: Session,
    order_id: str,
    *,
    session_id: str | None = None,
) -> dict:
    order = get_order(db, order_id)
    if not order:
        return {"success": False, "error": "Order not found"}

    if order["status"] == ORDER_STATUS["PAID"]:
        return {"success": False, "error": "Order is already paid"}

    items = _order_items_as_dict(db, order_id)
    policy = evaluate_transaction(
        db,
        items=items,
        buyer_id=str(order["buyer_id"]) if order.get("buyer_id") else None,
        merchant_id=str(order["merchant_id"]) if order.get("merchant_id") else None,
        order_id=order_id,
    )

    if session_id:
        log_audit(
            db,
            session_id=session_id,
            action="Payment Authorization",
            reason=policy["reason"],
            amount=policy["requested_amount"],
            authorization_status=policy["authorization_status"],
            policy_result=policy["policy_result"],
        )

    if not policy["allowed"]:
        return {"success": False, "policy": policy, "error": policy["reason"]}

    if not is_razorpay_configured():
        return {
            "success": False,
            "error": "Razorpay credentials are not configured",
            "policy": policy,
        }

    amount_paise = int(round(float(order["total_amount"]) * 100))

    try:
        client = get_razorpay_client()
        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": order["currency"],
            "receipt": str(order_id)[:40],
            "notes": {"order_id": order_id},
        })
    except Exception as exc:
        return {
            "success": False,
            "error": f"Razorpay order creation failed: {exc}",
            "policy": policy,
        }

    db.execute(
        text("""
            UPDATE orders
            SET razorpay_order_id = :razorpay_order_id,
                status = :status
            WHERE id::text = :order_id
        """),
        {
            "order_id": order_id,
            "razorpay_order_id": razorpay_order["id"],
            "status": ORDER_STATUS["PAYMENT_INITIATED"],
        },
    )

    payment_id = str(uuid4())
    db.execute(
        text("""
            INSERT INTO payments (id, order_id, status, amount)
            VALUES (:id, :order_id, :status, :amount)
        """),
        {
            "id": payment_id,
            "order_id": order_id,
            "status": "created",
            "amount": order["total_amount"],
        },
    )
    db.commit()

    return {
        "success": True,
        "policy": policy,
        "order_id": order_id,
        "razorpay_order_id": razorpay_order["id"],
        "amount": amount_paise,
        "currency": order["currency"],
        "key_id": settings.razorpay_key_id,
    }


def verify_payment(
    db: Session,
    *,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    session_id: str | None = None,
) -> dict:
    if not is_razorpay_configured():
        return {"success": False, "error": "Razorpay credentials are not configured"}

    client = get_razorpay_client()

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
    except Exception as exc:
        if session_id:
            log_audit(
                db,
                session_id=session_id,
                action="Payment Verification",
                reason=str(exc),
                authorization_status="blocked",
                policy_result="BLOCKED",
            )
        return {"success": False, "error": "Invalid payment signature"}

    order = get_order_by_razorpay_id(db, razorpay_order_id)
    if not order:
        return {"success": False, "error": "Order not found for Razorpay order ID"}

    db.execute(
        text("""
            UPDATE payments
            SET razorpay_payment_id = :razorpay_payment_id,
                status = :status
            WHERE order_id = :order_id
              AND status IN ('created', 'authorized')
        """),
        {
            "order_id": order["id"],
            "razorpay_payment_id": razorpay_payment_id,
            "status": "captured",
        },
    )
    update_order_status(db, str(order["id"]), ORDER_STATUS["PAID"])

    if session_id:
        log_audit(
            db,
            session_id=session_id,
            action="Payment Verification",
            reason="Signature verified",
            amount=float(order["total_amount"]),
            authorization_status="approved",
            policy_result="APPROVED",
        )

    return {
        "success": True,
        "order_id": str(order["id"]),
        "status": ORDER_STATUS["PAID"],
    }


def _ensure_webhook_table(db: Session) -> None:
    db.execute(
        text("""
            CREATE TABLE IF NOT EXISTS processed_webhook_events (
                event_id VARCHAR(100) PRIMARY KEY,
                event_type VARCHAR(100),
                payload JSONB DEFAULT '{}'::jsonb,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    )
    db.commit()


def _is_event_processed(db: Session, event_id: str) -> bool:
    row = db.execute(
        text("""
            SELECT event_id FROM processed_webhook_events
            WHERE event_id = :event_id
        """),
        {"event_id": event_id},
    ).fetchone()
    return row is not None


def _mark_event_processed(
    db: Session,
    event_id: str,
    event_type: str,
    payload: dict,
) -> None:
    db.execute(
        text("""
            INSERT INTO processed_webhook_events (event_id, event_type, payload)
            VALUES (:event_id, :event_type, CAST(:payload AS jsonb))
            ON CONFLICT (event_id) DO NOTHING
        """),
        {
            "event_id": event_id,
            "event_type": event_type,
            "payload": json.dumps(payload),
        },
    )
    db.commit()


def handle_webhook(
    db: Session,
    *,
    body: bytes,
    signature: str | None,
    event_id: str | None = None,
) -> dict:
    _ensure_webhook_table(db)

    if not is_razorpay_configured():
        return {"success": False, "error": "Razorpay credentials are not configured"}

    if not settings.razorpay_webhook_secret:
        return {"success": False, "error": "Webhook secret is not configured"}

    client = get_razorpay_client()
    body_str = body.decode("utf-8")

    try:
        client.utility.verify_webhook_signature(
            body_str,
            signature or "",
            settings.razorpay_webhook_secret,
        )
    except Exception as exc:
        return {"success": False, "error": f"Invalid webhook signature: {exc}"}

    payload = json.loads(body_str)
    resolved_event_id = event_id or payload.get("id")

    if not resolved_event_id:
        resolved_event_id = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
            .get("id")
        )

    if not resolved_event_id:
        resolved_event_id = f"{payload.get('event', 'unknown')}_{body_str[:64]}"

    if _is_event_processed(db, resolved_event_id):
        return {"success": True, "duplicate": True, "event_id": resolved_event_id}

    event_type = payload.get("event", "unknown")
    entity = _extract_payment_entity(payload)

    if entity:
        razorpay_order_id = entity.get("order_id")
        razorpay_payment_id = entity.get("id")
        order = get_order_by_razorpay_id(db, razorpay_order_id) if razorpay_order_id else None

        if order:
            if event_type in ("payment.captured", "order.paid"):
                db.execute(
                    text("""
                        UPDATE payments
                        SET razorpay_payment_id = :payment_id, status = 'captured'
                        WHERE order_id = :order_id
                    """),
                    {
                        "order_id": order["id"],
                        "payment_id": razorpay_payment_id,
                    },
                )
                update_order_status(db, str(order["id"]), ORDER_STATUS["PAID"])
                log_audit(
                    db,
                    session_id=None,
                    action=f"Webhook: {event_type}",
                    reason="Payment captured",
                    amount=float(order["total_amount"]),
                    authorization_status="approved",
                    policy_result="APPROVED",
                )

            elif event_type == "payment.failed":
                db.execute(
                    text("""
                        INSERT INTO payments (order_id, razorpay_payment_id, status, failure_reason, amount)
                        VALUES (:order_id, :payment_id, 'failed', :reason, :amount)
                    """),
                    {
                        "order_id": order["id"],
                        "payment_id": razorpay_payment_id,
                        "reason": entity.get("error_description", "Payment failed"),
                        "amount": float(order["total_amount"]),
                    },
                )
                update_order_status(db, str(order["id"]), ORDER_STATUS["PAYMENT_FAILED"])
                log_audit(
                    db,
                    session_id=None,
                    action=f"Webhook: {event_type}",
                    reason=entity.get("error_description", "Payment failed"),
                    amount=float(order["total_amount"]),
                    authorization_status="blocked",
                    policy_result="BLOCKED",
                )

            elif event_type == "payment.authorized":
                db.execute(
                    text("""
                        UPDATE payments
                        SET razorpay_payment_id = :payment_id, status = 'authorized'
                        WHERE order_id = :order_id AND status = 'created'
                    """),
                    {
                        "order_id": order["id"],
                        "payment_id": razorpay_payment_id,
                    },
                )

    _mark_event_processed(db, resolved_event_id, event_type, payload)
    return {"success": True, "event_id": resolved_event_id, "event_type": event_type}


def _extract_payment_entity(payload: dict) -> dict | None:
    payment = payload.get("payload", {}).get("payment", {})
    if isinstance(payment, dict):
        entity = payment.get("entity")
        if entity:
            return entity
    order = payload.get("payload", {}).get("order", {})
    if isinstance(order, dict):
        return order.get("entity")
    return None


def get_payment(db: Session, payment_id: str) -> dict | None:
    row = db.execute(
        text("""
            SELECT
                p.id, p.order_id, p.razorpay_payment_id, p.status,
                p.method, p.amount, p.failure_reason, p.created_at,
                o.razorpay_order_id, o.status AS order_status
            FROM payments p
            JOIN orders o ON o.id = p.order_id
            WHERE p.id::text = :payment_id
               OR p.razorpay_payment_id = :payment_id
            LIMIT 1
        """),
        {"payment_id": payment_id},
    ).fetchone()

    if not row:
        return None

    result = dict(row._mapping)
    if result.get("amount") is not None:
        result["amount"] = float(result["amount"])
    return result
