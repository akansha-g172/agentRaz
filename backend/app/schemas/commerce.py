"""Structured agentic commerce protocol messages."""

from pydantic import BaseModel, Field


class BuyerIntent(BaseModel):
    category: str | None = None
    max_price: float | None = None
    preferred_brands: list[str] = Field(default_factory=list)
    use_case: str | None = None
    preferences: list[str] = Field(default_factory=list)


class CommerceRequest(BaseModel):
    type: str = "commerce_request"
    buyer_id: str | None = None
    intent: BuyerIntent


class CommerceProduct(BaseModel):
    id: int
    name: str
    price: float
    brand: str | None = None


class CommerceAddon(BaseModel):
    id: int
    name: str
    price: float
    relationship_type: str
    confidence: float | None = None


class CommerceOffer(BaseModel):
    type: str = "commerce_offer"
    products: list[CommerceProduct]
    recommended_addons: list[CommerceAddon] = Field(default_factory=list)


class CartItemInput(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartCalculateRequest(BaseModel):
    items: list[CartItemInput]


class CartLineItem(BaseModel):
    product_id: int
    name: str
    brand: str | None = None
    quantity: int
    unit_price: float
    line_total: float
    in_stock: bool
    available_quantity: int


class CartCalculateResponse(BaseModel):
    items: list[CartLineItem]
    subtotal: float
    currency: str = "INR"


class CartValidationResult(BaseModel):
    valid: bool
    items: list[CartLineItem]
    subtotal: float
    currency: str = "INR"
    errors: list[str] = Field(default_factory=list)
