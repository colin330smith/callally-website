"""
Business Router - Dashboard APIs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional

from database.connection import get_db
from database.models import User, Business, Call, Appointment
from services.vapi_service import VapiService
from middleware.auth_middleware import get_current_user
from schemas.business import BusinessResponse, BusinessUpdate
from schemas.dashboard import (
    StatsResponse,
    CallResponse,
    CallListResponse,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse
)

router = APIRouter(prefix="/api/business", tags=["Business"])


async def get_business_for_user(
    business_id: UUID,
    user: User,
    db: AsyncSession
) -> Business:
    """Helper to get and verify business ownership."""
    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == user.id
        )
    )
    business = result.scalar_one_or_none()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    return business


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get business details."""
    business = await get_business_for_user(business_id, current_user, db)
    return BusinessResponse.model_validate(business)


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: UUID,
    request: BusinessUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update business settings."""
    business = await get_business_for_user(business_id, current_user, db)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(business, field, value)

    await db.commit()
    await db.refresh(business)

    # Update Vapi assistant if it exists
    if business.vapi_assistant_id:
        vapi = VapiService()
        await vapi.update_assistant(business.vapi_assistant_id, business)

    return BusinessResponse.model_validate(business)


@router.get("/{business_id}/stats", response_model=StatsResponse)
async def get_stats(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics."""
    business = await get_business_for_user(business_id, current_user, db)

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Total calls
    total_result = await db.execute(
        select(func.count(Call.id)).where(Call.business_id == business.id)
    )
    total_calls = total_result.scalar() or 0

    # Calls today
    today_result = await db.execute(
        select(func.count(Call.id)).where(
            and_(Call.business_id == business.id, Call.created_at >= today_start)
        )
    )
    calls_today = today_result.scalar() or 0

    # Calls this week
    week_result = await db.execute(
        select(func.count(Call.id)).where(
            and_(Call.business_id == business.id, Call.created_at >= week_start)
        )
    )
    calls_this_week = week_result.scalar() or 0

    # Calls this month
    month_result = await db.execute(
        select(func.count(Call.id)).where(
            and_(Call.business_id == business.id, Call.created_at >= month_start)
        )
    )
    calls_this_month = month_result.scalar() or 0

    # Appointments booked
    appt_result = await db.execute(
        select(func.count(Appointment.id)).where(Appointment.business_id == business.id)
    )
    appointments_booked = appt_result.scalar() or 0

    # Appointments this week
    appt_week_result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.business_id == business.id,
                Appointment.created_at >= week_start
            )
        )
    )
    appointments_this_week = appt_week_result.scalar() or 0

    # Average call duration
    avg_result = await db.execute(
        select(func.avg(Call.duration)).where(
            and_(Call.business_id == business.id, Call.duration.isnot(None))
        )
    )
    average_call_duration = avg_result.scalar() or 0.0

    # Missed calls
    missed_result = await db.execute(
        select(func.count(Call.id)).where(
            and_(Call.business_id == business.id, Call.status == "missed")
        )
    )
    missed_calls = missed_result.scalar() or 0

    # Voicemails
    vm_result = await db.execute(
        select(func.count(Call.id)).where(
            and_(Call.business_id == business.id, Call.status == "voicemail")
        )
    )
    voicemails = vm_result.scalar() or 0

    return StatsResponse(
        total_calls=total_calls,
        calls_today=calls_today,
        calls_this_week=calls_this_week,
        calls_this_month=calls_this_month,
        appointments_booked=appointments_booked,
        appointments_this_week=appointments_this_week,
        average_call_duration=round(average_call_duration, 1),
        missed_calls=missed_calls,
        voicemails=voicemails
    )


@router.get("/{business_id}/calls", response_model=CallListResponse)
async def get_calls(
    business_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get call history with pagination."""
    business = await get_business_for_user(business_id, current_user, db)

    # Get total count
    count_result = await db.execute(
        select(func.count(Call.id)).where(Call.business_id == business.id)
    )
    total = count_result.scalar() or 0

    # Get paginated calls
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Call)
        .where(Call.business_id == business.id)
        .order_by(Call.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    calls = result.scalars().all()

    return CallListResponse(
        calls=[CallResponse.model_validate(c) for c in calls],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(offset + len(calls)) < total
    )


@router.get("/{business_id}/calls/{call_id}", response_model=CallResponse)
async def get_call(
    business_id: UUID,
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single call details."""
    business = await get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Call).where(
            and_(Call.id == call_id, Call.business_id == business.id)
        )
    )
    call = result.scalar_one_or_none()

    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )

    return CallResponse.model_validate(call)


@router.post("/{business_id}/test-call")
async def initiate_test_call(
    business_id: UUID,
    phone_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initiate a test call to verify AI assistant."""
    business = await get_business_for_user(business_id, current_user, db)

    if not business.vapi_assistant_id or not business.vapi_phone_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI assistant not set up yet"
        )

    vapi = VapiService()
    call_id = await vapi.make_test_call(
        assistant_id=business.vapi_assistant_id,
        phone_number=phone_number,
        phone_id=business.vapi_phone_id
    )

    if not call_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate test call"
        )

    return {"call_id": call_id, "message": "Test call initiated"}


@router.get("/{business_id}/appointments", response_model=AppointmentListResponse)
async def get_appointments(
    business_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get appointments with pagination."""
    business = await get_business_for_user(business_id, current_user, db)

    # Build query
    query = select(Appointment).where(Appointment.business_id == business.id)
    count_query = select(func.count(Appointment.id)).where(Appointment.business_id == business.id)

    if status:
        query = query.where(Appointment.status == status)
        count_query = count_query.where(Appointment.status == status)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated appointments
    offset = (page - 1) * per_page
    result = await db.execute(
        query
        .order_by(Appointment.appointment_date.desc())
        .offset(offset)
        .limit(per_page)
    )
    appointments = result.scalars().all()

    return AppointmentListResponse(
        appointments=[AppointmentResponse.model_validate(a) for a in appointments],
        total=total,
        page=page,
        per_page=per_page,
        has_more=(offset + len(appointments)) < total
    )


@router.post("/{business_id}/appointments", response_model=AppointmentResponse)
async def create_appointment(
    business_id: UUID,
    request: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new appointment."""
    business = await get_business_for_user(business_id, current_user, db)

    from uuid import uuid4
    appointment = Appointment(
        id=uuid4(),
        business_id=business.id,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        customer_email=request.customer_email,
        customer_address=request.customer_address,
        service_type=request.service_type,
        appointment_date=request.appointment_date,
        duration_minutes=request.duration_minutes,
        notes=request.notes,
        status="scheduled"
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    return AppointmentResponse.model_validate(appointment)


@router.patch("/{business_id}/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    business_id: UUID,
    appointment_id: UUID,
    request: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an appointment."""
    business = await get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Appointment).where(
            and_(Appointment.id == appointment_id, Appointment.business_id == business.id)
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value.value if hasattr(value, 'value') else value)

    await db.commit()
    await db.refresh(appointment)

    return AppointmentResponse.model_validate(appointment)


@router.delete("/{business_id}/appointments/{appointment_id}")
async def delete_appointment(
    business_id: UUID,
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an appointment."""
    business = await get_business_for_user(business_id, current_user, db)

    result = await db.execute(
        select(Appointment).where(
            and_(Appointment.id == appointment_id, Appointment.business_id == business.id)
        )
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await db.delete(appointment)
    await db.commit()

    return {"message": "Appointment deleted"}
