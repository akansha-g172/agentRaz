"""Critical business-logic tests for agentic commerce MVP."""

from uuid import uuid4

from app.core.database import SessionLocal
from app.services.cart_service import calculate_cart, validate_cart
from app.services.catalog_service import check_inventory
from app.services.recommendation_service import recommend_products
from app.schemas.commerce import CommerceRequest, BuyerIntent
from app.agents.merchant_agent import handle_commerce_request
from app.policies.policy_engine import evaluate_transaction
from app.services.order_service import create_order
from app.razorpay.service import (
    verify_payment,
    _ensure_webhook_table,
    _is_event_processed,
    _mark_event_processed,
)
from app.razorpay.client import is_razorpay_configured


def test_hard_budget_constraint():
    db = SessionLocal()
    try:
        recs = recommend_products(
            db,
            category="Laptop",
            max_price=65000,
            preferred_brands=["Lenovo"],
            use_case="coding",
        )
        assert all(r["price"] <= 65000 for r in recs)
        assert all(r["product_id"] != 2 for r in recs)  # CodeMaster X15 = 68999
    finally:
        db.close()


def test_out_of_stock_cannot_be_purchased():
    db = SessionLocal()
    try:
        # Temporarily zero out stock for product 1
        db.execute(
            __import__("sqlalchemy").text(
                "UPDATE inventory SET stock_quantity = 0 WHERE product_id = 1"
            )
        )
        db.commit()

        result = check_inventory(db, 1, quantity=1)
        assert result["available"] is False
        assert "stock" in result["reason"].lower()

        validation = validate_cart(db, [{"product_id": 1, "quantity": 1}])
        assert validation["valid"] is False
    finally:
        db.execute(
            __import__("sqlalchemy").text(
                "UPDATE inventory SET stock_quantity = 20 WHERE product_id = 1"
            )
        )
        db.commit()
        db.close()


def test_cart_uses_database_prices():
    db = SessionLocal()
    try:
        cart = calculate_cart(
            db,
            [{"product_id": 3, "quantity": 1}, {"product_id": 10, "quantity": 2}],
        )
        assert cart["subtotal"] == 59999 + (999 * 2)
        assert cart["currency"] == "INR"
        assert len(cart["items"]) == 2
    finally:
        db.close()


def test_merchant_commerce_offer_structure():
    db = SessionLocal()
    try:
        request = CommerceRequest(
            buyer_id="demo",
            intent=BuyerIntent(
                category="Laptop",
                max_price=65000,
                preferred_brands=["Lenovo"],
                use_case="coding",
            ),
        )
        result = handle_commerce_request(db, request)
        assert result["offer"]["type"] == "commerce_offer"
        assert isinstance(result["offer"]["products"], list)
        for product in result["offer"]["products"]:
            assert product["price"] <= 65000
    finally:
        db.close()


def test_policy_approved_within_limit():
    db = SessionLocal()
    try:
        # DevBook Air (59999) + SwiftMouse (999) = 60998 <= 70000
        result = evaluate_transaction(
            db,
            items=[{"product_id": 3, "quantity": 1}, {"product_id": 10, "quantity": 1}],
        )
        assert result["allowed"] is True
        assert result["policy_result"] == "APPROVED"
    finally:
        db.close()


def test_policy_blocked_over_limit():
    db = SessionLocal()
    try:
        # CodeMaster X15 (68999) + mouse + sleeve = 71497 > 70000
        result = evaluate_transaction(
            db,
            items=[
                {"product_id": 2, "quantity": 1},
                {"product_id": 9, "quantity": 1},
                {"product_id": 16, "quantity": 1},
            ],
        )
        assert result["allowed"] is False
        assert result["policy_result"] == "BLOCKED"
        assert result["requested_amount"] > result["limit"]
    finally:
        db.close()


def test_invalid_payment_signature_rejected():
    if not is_razorpay_configured():
        return

    db = SessionLocal()
    try:
        result = verify_payment(
            db,
            razorpay_order_id="order_test123",
            razorpay_payment_id="pay_test123",
            razorpay_signature="invalid_signature",
        )
        assert result["success"] is False
        assert "signature" in result["error"].lower()
    finally:
        db.close()


def test_webhook_event_processed_only_once():
    db = SessionLocal()
    try:
        _ensure_webhook_table(db)
        event_id = f"evt_test_{uuid4()}"
        assert _is_event_processed(db, event_id) is False
        _mark_event_processed(db, event_id, "payment.captured", {"test": True})
        assert _is_event_processed(db, event_id) is True
    finally:
        db.close()


def test_max_retry_attempts_blocks_payment():
    db = SessionLocal()
    try:
        order_result = create_order(
            db,
            items=[{"product_id": 10, "quantity": 1}],
        )
        assert order_result["success"] is True
        order_id = str(order_result["order"]["id"])

        for _ in range(2):
            db.execute(
                __import__("sqlalchemy").text("""
                    INSERT INTO payments (order_id, status, amount, failure_reason)
                    VALUES (:order_id, 'failed', 999, 'Simulated failure')
                """),
                {"order_id": order_id},
            )
        db.commit()

        policy = evaluate_transaction(
            db,
            items=[{"product_id": 10, "quantity": 1}],
            order_id=order_id,
        )
        assert policy["allowed"] is False
        assert any("retry" in err.lower() for err in policy["errors"])
    finally:
        db.close()
