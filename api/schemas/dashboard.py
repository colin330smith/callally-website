"""
Dashboard Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from enum import Enum


class CallStatus(str, Enum):
    COMPLETED = "completed"
    MISSED = "missed"
    VOICEMAIL = "voicemail"
    IN_PROGRESS = "in_progress"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class StatsResponse(BaseModel):
    """Response model for dashboard statistics."""
    total_calls: int
    calls_today: int
    calls_this_week: int
    calls_this_month: int
    appointments_booked: int
    appointments_this_week: int
    average_call_duration: float
    missed_calls: int
    voicemails: int


class CallResponse(BaseModel):
    """Response model for a single call."""
    id: UUID
    business_id: UUID
    vapi_call_id: str
    caller_phone: str
    caller_name: Optional[str] = None
    status: str
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    recording_url: Optional[str] = None
    appointment_booked: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    """Response model for paginated call list."""
    calls: List[CallResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


class AppointmentCreate(BaseModel):
    """Request model for creating an appointment."""
    customer_name: str
    customer_phone: str
    customer_email: Optional[EmailStr] = None
    service_type: str
    appointment_date: date
    appointment_time: str
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Request model for updating an appointment."""
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    service_type: Optional[str] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Response model for a single appointment."""
    id: UUID
    business_id: UUID
    call_id: Optional[UUID] = None
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    service_type: str
    appointment_date: date
    appointment_time: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Response model for paginated appointment list."""
    appointments: List[AppointmentResponse]
    total: int
    page: int
    per_page: int
    has_more: bool
