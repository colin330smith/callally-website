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
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Services
    services: Optional[List[str]] = None
    custom_services: Optional[str] = None
    service_area: Optional[str] = None

    # AI Agent
    agent_name: Optional[str] = None
    agent_voice: Optional[str] = None
    greeting_style: Optional[str] = None

    # Business Hours
    business_hours: Optional[Dict[str, str]] = None

    # Emergency
    emergency_dispatch: bool = False
    emergency_keywords: Optional[List[str]] = None
    emergency_phones: Optional[List[str]] = None

    # Appointments
    appointment_types: Optional[List[str]] = None
    appointment_duration: int = 30

    # Vapi
    vapi_assistant_id: Optional[str] = None
    vapi_phone_id: Optional[str] = None
    vapi_phone_number: Optional[str] = None

    # Subscription
    stripe_customer_id: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    trial_ends_at: Optional[datetime] = None

    # Onboarding
    onboarding_step: int = 1
    onboarding_complete: bool = False

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
