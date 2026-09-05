"""Deterministic policy engine — LLMs cannot bypass these checks."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.cart_service import validate_cart


def _get_buyer(db: Session, buyer_id: str | None) -> dict | None:
    if not buyer_id:
        row = db.execute(
            text("""
                SELECT id, name, preferences, spending_limit
                FROM buyers
                ORDER BY created_at
                LIMIT 1
            """)
        ).fetchone()
    else:
        row = db.execute(
            text("""
                SELECT id, name, preferences, spending_limit
                FROM buyers
                WHERE id::text = :buyer_id
                   OR name = :buyer_id
                LIMIT 1
            """),
            {"buyer_id": buyer_id},
        ).fetchone()

    return dict(row._mapping) if row else None


def _get_merchant_policy(db: Session, merchant_id: str | None) -> dict | None:
    if not merchant_id:
        row = db.execute(
            text("""
                SELECT
                    merchant_id,
                    max_transaction_amount,
                    max_discount_percent,
                    max_retry_attempts,
                    allow_upsell,
                    require_confirmation_above
                FROM merchant_policies
                ORDER BY created_at
                LIMIT 1
            """)
        ).fetchone()
    else:
        row = db.execute(
            text("""
                SELECT
                    merchant_id,
                    max_transaction_amount,
                    max_discount_percent,
                    max_retry_attempts,
                    allow_upsell,
                    require_confirmation_above
                FROM merchant_policies
                WHERE merchant_id::text = :merchant_id
                LIMIT 1
            """),
            {"merchant_id": merchant_id},
        ).fetchone()

    return dict(row._mapping) if row else None


def _count_failed_payments(db: Session, order_id: str) -> int:
    row = db.execute(
        text("""
            SELECT COUNT(*) AS cnt
            FROM payments
            WHERE order_id::text = :order_id
              AND status IN ('failed', 'payment_failed')
        """),
        {"order_id": order_id},
    ).fetchone()
    return int(row.cnt if row else 0)


def evaluate_transaction(
    db: Session,
    *,
    items: list[dict],
    buyer_id: str | None = None,
    merchant_id: str | None = None,
    currency: str = "INR",
    includes_upsell: bool = False,
    order_id: str | None = None,
) -> dict:
    """
    Validate a transaction against buyer limits, merchant policy,
    inventory, and retry rules.
    """
    cart_validation = validate_cart(db, items)
    requested_amount = float(cart_validation["subtotal"])

    buyer = _get_buyer(db, buyer_id)
    policy = _get_merchant_policy(db, merchant_id)

    buyer_limit = float(buyer["spending_limit"]) if buyer and buyer.get("spending_limit") is not None else settings.max_transaction_amount
    merchant_limit = float(policy["max_transaction_amount"]) if policy and policy.get("max_transaction_amount") is not None else settings.max_transaction_amount
    effective_limit = min(buyer_limit, merchant_limit)

    max_retries = int(policy["max_retry_attempts"]) if policy and policy.get("max_retry_attempts") is not None else settings.max_retry_attempts
    allow_upsell = bool(policy["allow_upsell"]) if policy else True
    require_confirmation_above = (
        float(policy["require_confirmation_above"])
        if policy and policy.get("require_confirmation_above") is not None
        else None
    )

    errors: list[str] = []
    authorization_status = "approved"

    if not cart_validation["valid"]:
        errors.extend(cart_validation["errors"])
        authorization_status = "blocked"

    if currency != "INR":
        errors.append(f"Unsupported currency: {currency}")
        authorization_status = "blocked"

    if requested_amount > effective_limit:
        errors.append("Transaction exceeds buyer authorization limit")
        authorization_status = "blocked"

    if includes_upsell and not allow_upsell:
        errors.append("Upsell items are not permitted by merchant policy")
        authorization_status = "blocked"

    if order_id:
        failed_attempts = _count_failed_payments(db, order_id)
        if failed_attempts >= max_retries:
            errors.append("Maximum payment retry attempts exceeded")
            authorization_status = "blocked"

    requires_confirmation = (
        require_confirmation_above is not None
        and requested_amount > require_confirmation_above
    )

    allowed = len(errors) == 0

    return {
        "allowed": allowed,
        "reason": errors[0] if errors else "Transaction approved",
        "errors": errors,
        "limit": effective_limit,
        "requested_amount": requested_amount,
        "currency": currency,
        "authorization_status": authorization_status,
        "policy_result": "APPROVED" if allowed else "BLOCKED",
        "requires_confirmation": requires_confirmation,
        "cart": cart_validation,
        "buyer_id": str(buyer["id"]) if buyer else None,
        "merchant_id": str(policy["merchant_id"]) if policy else merchant_id,
    }
