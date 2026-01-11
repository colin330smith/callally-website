"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re


class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: EmailStr
    password: str
    business_name: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    @field_validator('business_name')
    @classmethod
    def validate_business_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Business name must be at least 2 characters')
        if len(v) > 255:
            raise ValueError('Business name must be less than 255 characters')
        return v


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
