"""Controlled cart tools — prices and stock from backend only."""

from sqlalchemy.orm import Session

from app.services.cart_service import calculate_cart, validate_cart


def calculate_cart_total(db: Session, items: list[dict]) -> dict:
    return calculate_cart(db, items)


def validate_cart_items(db: Session, items: list[dict]) -> dict:
    return validate_cart(db, items)
