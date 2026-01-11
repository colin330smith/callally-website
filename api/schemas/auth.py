"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: EmailStr
    password: str
    business_name: str


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    business_id: Optional[UUID] = None


class UserResponse(BaseModel):
    """Response model for user data."""
    id: UUID
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BusinessSummary(BaseModel):
    """Summary of a business for user response."""
    id: UUID
    name: str
    onboarding_step: int
    status: str
    subscription_status: Optional[str] = None
    vapi_phone_number: Optional[str] = None

    class Config:
        from_attributes = True


class UserWithBusinessesResponse(BaseModel):
    """Response model for user with their businesses."""
    user: UserResponse
    businesses: List[BusinessSummary]
