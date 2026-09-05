from google import genai

from app.core.config import settings


client = genai.Client(
    api_key=settings.gemini_api_key
)


INTENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "category": {
            "type": "STRING",
            "nullable": True
        },
        "max_price": {
            "type": "NUMBER",
            "nullable": True
        },
        "preferred_brands": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        },
        "use_case": {
            "type": "STRING",
            "nullable": True
        },
        "preferences": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        }
    },
    "required": [
        "category",
        "max_price",
        "preferred_brands",
        "use_case",
        "preferences"
    ]
}

def extract_buyer_intent(user_message: str) -> dict:

    response = client.models.generate_content(
        model=settings.gemini_model,

        contents=f"""
You are the Buyer Intent Agent for an agentic commerce system.

Your ONLY responsibility is to convert the buyer's natural-language
request into structured shopping intent.

Do NOT recommend products.
Do NOT invent product information.
Do NOT make purchases.
Do NOT modify prices.
Do NOT make payment decisions.

Extract only information explicitly stated or strongly implied
by the buyer.

Rules:
- category should be a concise product category such as Laptop,
  Monitor, Keyboard, Mouse, Headphones, etc.
- max_price should be the buyer's stated maximum budget.
- preferred_brands should contain explicitly preferred brands.
- use_case should describe the main purpose, such as coding,
  gaming, productivity, travel, or meetings.
- preferences should contain additional requirements such as
  lightweight, portable, large screen, wireless, etc.
- Use null when a value cannot be determined.

Buyer request:
{user_message}
""",

        config={
            "response_mime_type": "application/json",
            "response_schema": INTENT_SCHEMA,
        },
    )

    return response.parsed