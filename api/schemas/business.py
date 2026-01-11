"""
Business and Onboarding Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class BusinessCreate(BaseModel):
    """Request model for creating a business."""
    name: str


class BusinessUpdate(BaseModel):
    """Request model for updating a business."""
    name: Optional[str] = None
    industry: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class OnboardingStepRequest(BaseModel):
    """Request model for saving onboarding step data."""
    step: int
    data: Dict[str, Any]


class BusinessResponse(BaseModel):
    """Response model for business data."""
    id: UUID
    user_id: UUID
    name: str
    industry: Optional[str] = None
    phone: Optional[str] = None
    service_area: Optional[str] = None

    # Services & hours
    services: Optional[List[Any]] = None
    custom_services: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None

    # Call handling
    call_mode: str = "forwarding"
    rings_before_ai: int = 3
    emergency_dispatch: bool = False
    emergency_phones: Optional[List[Any]] = None
    emergency_keywords: Optional[List[Any]] = None

    # AI config
    agent_name: str = "Alex"
    agent_voice: str = "rachel"
    appointment_types: Optional[List[Any]] = None

    # Notifications
    notification_email: Optional[str] = None
    notification_phone: Optional[str] = None

    # Vapi integration
    vapi_assistant_id: Optional[str] = None
    vapi_phone_id: Optional[str] = None
    vapi_phone_number: Optional[str] = None

    # Stripe integration
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    minutes_used: int = 0
    minutes_limit: int = 100

    # Status
    status: str = "onboarding"
    onboarding_step: int = 0

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OnboardingCompleteResponse(BaseModel):
    """Response model for onboarding completion."""
    success: bool
    business_id: UUID
    phone_number: Optional[str] = None
    assistant_id: Optional[str] = None
    message: str
