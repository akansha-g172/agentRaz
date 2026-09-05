"""Critical business-logic tests for agentic commerce MVP."""

from app.core.database import SessionLocal
from app.services.cart_service import calculate_cart, validate_cart
from app.services.catalog_service import check_inventory
from app.services.recommendation_service import recommend_products
from app.schemas.commerce import CommerceRequest, BuyerIntent
from app.agents.merchant_agent import handle_commerce_request


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
