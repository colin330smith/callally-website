"""
CallAlly API Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/callally")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Vapi
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
VAPI_WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET", "")

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Stripe Price IDs (set these after creating products in Stripe)
STRIPE_PRICES = {
    "starter": os.getenv("STRIPE_PRICE_STARTER", ""),
    "professional": os.getenv("STRIPE_PRICE_PROFESSIONAL", ""),
    "business": os.getenv("STRIPE_PRICE_BUSINESS", ""),
}

# Plan limits
PLAN_LIMITS = {
    "starter": {"price": 4900, "minutes": 100},
    "professional": {"price": 9900, "minutes": 300},
    "business": {"price": 19900, "minutes": 1000},
}

# Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "CallAlly <hello@callallynow.com>")

# App
BASE_URL = os.getenv("BASE_URL", "https://callallynow.com")
API_URL = os.getenv("API_URL", "https://api.callallynow.com")
PORT = os.getenv("PORT", "8000")
