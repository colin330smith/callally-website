"""
SQLAlchemy ORM Models for CallAlly
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    businesses: Mapped[List["Business"]] = relationship("Business", back_populates="user", cascade="all, delete-orphan")


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Basic info (signup + onboarding step 1)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    service_area: Mapped[Optional[str]] = mapped_column(Text)

    # Services & hours (onboarding step 2)
    services: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    custom_services: Mapped[Optional[str]] = mapped_column(Text)
    business_hours: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Call handling (onboarding step 3)
    call_mode: Mapped[str] = mapped_column(String(20), default="forwarding")
    rings_before_ai: Mapped[int] = mapped_column(Integer, default=3)
    emergency_dispatch: Mapped[bool] = mapped_column(Boolean, default=False)
    emergency_phones: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    emergency_keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)

    # AI config (onboarding step 4)
    agent_name: Mapped[str] = mapped_column(String(50), default="Alex")
    agent_voice: Mapped[str] = mapped_column(String(50), default="rachel")
    appointment_types: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)

    # Notifications (onboarding step 5)
    notification_email: Mapped[Optional[str]] = mapped_column(String(255))
    notification_phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Vapi integration
    vapi_assistant_id: Mapped[Optional[str]] = mapped_column(String(100))
    vapi_phone_id: Mapped[Optional[str]] = mapped_column(String(100))
    vapi_phone_number: Mapped[Optional[str]] = mapped_column(String(20))

    # Stripe integration
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(100))
    subscription_plan: Mapped[Optional[str]] = mapped_column(String(50))
    subscription_status: Mapped[Optional[str]] = mapped_column(String(50))
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    minutes_used: Mapped[int] = mapped_column(Integer, default=0)
    minutes_limit: Mapped[int] = mapped_column(Integer, default=100)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="onboarding")
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="businesses")
    calls: Mapped[List["Call"]] = relationship("Call", back_populates="business", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="business", cascade="all, delete-orphan")
    sms_messages: Mapped[List["SMSMessage"]] = relationship("SMSMessage", back_populates="business", cascade="all, delete-orphan")
    integrations: Mapped[List["Integration"]] = relationship("Integration", back_populates="business", cascade="all, delete-orphan")


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    vapi_call_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)

    # Call details
    caller_phone: Mapped[Optional[str]] = mapped_column(String(20))
    caller_name: Mapped[Optional[str]] = mapped_column(String(255))
    direction: Mapped[str] = mapped_column(String(10), default="inbound")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration: Mapped[Optional[int]] = mapped_column(Integer)  # seconds

    # Call outcome
    status: Mapped[Optional[str]] = mapped_column(String(50))
    appointment_booked: Mapped[bool] = mapped_column(Boolean, default=False)
    callback_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    emergency_triggered: Mapped[bool] = mapped_column(Boolean, default=False)

    # Content
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    recording_url: Mapped[Optional[str]] = mapped_column(Text)

    # Extracted data
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="calls")
    appointment: Mapped[Optional["Appointment"]] = relationship("Appointment", back_populates="call", uselist=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    call_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=True)

    # Customer info
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20))
    customer_email: Mapped[Optional[str]] = mapped_column(String(255))
    customer_address: Mapped[Optional[str]] = mapped_column(Text)

    # Appointment details
    service_type: Mapped[Optional[str]] = mapped_column(String(100))
    appointment_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="appointments")
    call: Mapped[Optional["Call"]] = relationship("Call", back_populates="appointment")


class SMSMessage(Base):
    __tablename__ = "sms_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # inbound/outbound
    body: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="sent")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="sms_messages")


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="disconnected")
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    config: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business: Mapped["Business"] = relationship("Business", back_populates="integrations")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    record_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    minutes_used: Mapped[float] = mapped_column(Integer, default=0)
    appointments_booked: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
