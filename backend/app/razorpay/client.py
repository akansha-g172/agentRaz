import razorpay

from app.core.config import settings


def get_razorpay_client() -> razorpay.Client:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise ValueError("Razorpay credentials are not configured")
    return razorpay.Client(
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
    )


def is_razorpay_configured() -> bool:
    return bool(settings.razorpay_key_id and settings.razorpay_key_secret)
