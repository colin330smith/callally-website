"""
CallAlly Sales Engine Configuration
====================================
Configure all API keys and settings here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Resend for email
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
# Using verified domain - switch to callallynow.com once DNS is set up
FROM_EMAIL = "colin@localliftleads.com"
REPLY_TO = "colin@localliftleads.com"

# Twilio for SMS
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE = os.getenv("TWILIO_PHONE", "")

# Vapi for AI calls
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "")

# Database
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "sales.db")

# Lead sources
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
YELP_API_KEY = os.getenv("YELP_API_KEY", "")

# CallAlly signup URL
SIGNUP_URL = "https://callallynow.com/signup"

# Verticals and search terms
VERTICALS = {
    "hvac": ["hvac", "air conditioning", "heating cooling", "ac repair", "furnace repair"],
    "plumber": ["plumber", "plumbing", "drain cleaning", "water heater"],
    "electrician": ["electrician", "electrical contractor", "electrical repair"],
    "dental": ["dentist", "dental office", "dental practice"],
    "roofing": ["roofing", "roof repair", "roofer"],
    "garage_door": ["garage door repair", "garage door service"],
    "locksmith": ["locksmith", "lock repair"],
    "pest_control": ["pest control", "exterminator"],
    "landscaping": ["landscaping", "lawn care", "lawn service"],
    "cleaning": ["cleaning service", "maid service", "janitorial"],
}

# Target cities (start small, expand)
TARGET_CITIES = [
    # California
    ("San Francisco", "CA"),
    ("Los Angeles", "CA"),
    ("San Diego", "CA"),
    ("Sacramento", "CA"),
    # Texas
    ("Houston", "TX"),
    ("Dallas", "TX"),
    ("Austin", "TX"),
    ("San Antonio", "TX"),
    # Florida
    ("Miami", "FL"),
    ("Tampa", "FL"),
    ("Orlando", "FL"),
    # Arizona
    ("Phoenix", "AZ"),
    ("Scottsdale", "AZ"),
    ("Tucson", "AZ"),
    # Others
    ("Denver", "CO"),
    ("Seattle", "WA"),
    ("Portland", "OR"),
    ("Las Vegas", "NV"),
    ("Atlanta", "GA"),
    ("Charlotte", "NC"),
]

# Outreach settings
DAILY_EMAIL_LIMIT = 100  # Start conservative
DAILY_CALL_LIMIT = 50
DAILY_SMS_LIMIT = 50

# Follow-up timing (days)
FOLLOWUP_SCHEDULE = [0, 2, 4, 7, 14, 21]  # Days between touches
