"""Merchant-side commerce orchestration.

The Merchant Agent uses Gemini to choose tool actions, but all product data,
pricing, inventory, and recommendations come from deterministic backend tools.
"""

from __future__ import annotations

import json

from google import genai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.commerce import (
    CommerceAddon,
    CommerceOffer,
    CommerceProduct,
    CommerceRequest,
)
from app.tools import catalog_tools, cart_tools


client = genai.Client(api_key=settings.gemini_api_key)

# Tools the merchant agent may request — backend executes them.
MERCHANT_TOOLS = [
    "search_catalog",
    "get_product",
    "check_inventory",
    "get_recommendations",
    "get_product_addons",
    "calculate_cart",
]

TOOL_PLAN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "tools_to_call": {
            "type": "ARRAY",
            "items": {
                "type": "STRING",
                "enum": MERCHANT_TOOLS,
            },
        },
        "reasoning_summary": {
            "type": "STRING",
            "description": "Brief structured explanation of merchant actions (no hidden chain-of-thought).",
        },
    },
    "required": ["tools_to_call", "reasoning_summary"],
}


def _default_tool_plan() -> list[str]:
    return ["get_recommendations", "get_product_addons"]


def plan_merchant_actions(commerce_request: CommerceRequest) -> dict:
    """Ask Gemini which controlled tools to invoke for this commerce request."""
    intent = commerce_request.intent

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=f"""
You are the Merchant Agent for an agentic commerce platform.

Given a structured buyer commerce request, decide which backend tools
should be invoked. You must NOT invent products, prices, or inventory.

Available tools:
- search_catalog: browse catalog with filters
- get_product: fetch a specific product by ID
- check_inventory: verify stock for a product
- get_recommendations: rank products for buyer intent (preferred for offers)
- get_product_addons: upsell/cross-sell for a chosen product
- calculate_cart: compute totals when line items are known

Rules:
- For a new shopping intent with no cart items, prefer get_recommendations
  and get_product_addons.
- Never choose payment or order creation tools (not available).
- Return only tool names from the allowed list.

Commerce request:
{json.dumps(commerce_request.model_dump(), indent=2)}
""",
            config={
                "response_mime_type": "application/json",
                "response_schema": TOOL_PLAN_SCHEMA,
            },
        )
        plan = response.parsed
        if isinstance(plan, dict):
            return plan
        if hasattr(plan, "model_dump"):
            return plan.model_dump()
        return dict(plan)
    except Exception:
        return {
            "tools_to_call": _default_tool_plan(),
            "reasoning_summary": "Default recommendation and addon lookup.",
        }


def handle_commerce_request(
    db: Session,
    commerce_request: CommerceRequest,
    *,
    recommendation_limit: int = 3,
    addon_limit: int = 3,
) -> dict:
    """
    Execute the agentic commerce protocol:
      commerce_request → tool execution → commerce_offer
    """
    intent = commerce_request.intent
    plan = plan_merchant_actions(commerce_request)
    tools_called = plan.get("tools_to_call") or _default_tool_plan()

    # Normalize unknown tool names.
    tools_called = [t for t in tools_called if t in MERCHANT_TOOLS]
    if not tools_called:
        tools_called = _default_tool_plan()

    tool_results: dict = {}
    products: list[CommerceProduct] = []
    addons: list[CommerceAddon] = []
    seen_addon_ids: set[int] = set()

    for tool in tools_called:
        if tool == "search_catalog":
            result = catalog_tools.search_catalog(
                db,
                category=intent.category,
                max_price=intent.max_price,
                brand=intent.preferred_brands[0] if intent.preferred_brands else None,
                limit=recommendation_limit,
            )
            tool_results["search_catalog"] = result

        elif tool == "get_recommendations":
            result = catalog_tools.get_recommendations(
                db,
                category=intent.category,
                max_price=intent.max_price,
                preferred_brands=intent.preferred_brands,
                use_case=intent.use_case,
                preferences=intent.preferences,
                limit=recommendation_limit,
            )
            tool_results["get_recommendations"] = result

            for rec in result.get("recommendations", []):
                products.append(
                    CommerceProduct(
                        id=rec["product_id"],
                        name=rec["name"],
                        price=rec["price"],
                        brand=rec.get("brand"),
                    )
                )

        elif tool == "get_product_addons" and products:
            primary_id = products[0].id
            result = catalog_tools.get_product_addons(
                db, primary_id, limit=addon_limit
            )
            tool_results["get_product_addons"] = result

            for addon in result.get("addons", []):
                addon_id = addon["id"]
                if addon_id in seen_addon_ids:
                    continue
                seen_addon_ids.add(addon_id)
                addons.append(
                    CommerceAddon(
                        id=addon_id,
                        name=addon["name"],
                        price=addon["price"],
                        relationship_type=addon["relationship_type"],
                        confidence=addon.get("confidence"),
                    )
                )

        elif tool == "check_inventory" and products:
            checks = []
            for product in products[:3]:
                checks.append(
                    catalog_tools.check_product_inventory(db, product.id, 1)
                )
            tool_results["check_inventory"] = checks

        elif tool == "calculate_cart" and products:
            items = [{"product_id": p.id, "quantity": 1} for p in products]
            tool_results["calculate_cart"] = cart_tools.calculate_cart_total(
                db, items
            )

    # If Gemini skipped recommendations, run them deterministically.
    if not products:
        recs = catalog_tools.get_recommendations(
            db,
            category=intent.category,
            max_price=intent.max_price,
            preferred_brands=intent.preferred_brands,
            use_case=intent.use_case,
            preferences=intent.preferences,
            limit=recommendation_limit,
        )
        tool_results["get_recommendations_fallback"] = recs
        for rec in recs.get("recommendations", []):
            products.append(
                CommerceProduct(
                    id=rec["product_id"],
                    name=rec["name"],
                    price=rec["price"],
                    brand=rec.get("brand"),
                )
            )

    # Fetch addons for top product if not already loaded.
    if products and not addons:
        addon_result = catalog_tools.get_product_addons(
            db, products[0].id, limit=addon_limit
        )
        tool_results["get_product_addons_fallback"] = addon_result
        for addon in addon_result.get("addons", []):
            addons.append(
                CommerceAddon(
                    id=addon["id"],
                    name=addon["name"],
                    price=addon["price"],
                    relationship_type=addon["relationship_type"],
                    confidence=addon.get("confidence"),
                )
            )

    offer = CommerceOffer(products=products, recommended_addons=addons)

    return {
        "request": commerce_request.model_dump(),
        "plan": plan,
        "tools_called": tools_called,
        "tool_results": tool_results,
        "offer": offer.model_dump(),
    }
