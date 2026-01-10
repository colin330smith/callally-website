"""
Webhooks Router - Stripe and Vapi event handlers
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

from database.connection import get_db
from database.models import Business, Call, Appointment, UsageRecord
from services.stripe_service import StripeService
from services.email_service import EmailService
import config

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle Stripe webhook events.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature"
        )

    event = StripeService.verify_webhook_signature(payload, signature)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    if event_type == "customer.subscription.created":
        await handle_subscription_created(data, db)
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(data, db)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(data, db)
    elif event_type == "invoice.payment_succeeded":
        await handle_payment_succeeded(data, db)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(data, db)

    return {"received": True}


async def handle_subscription_created(data: Dict[str, Any], db: AsyncSession):
    """Handle new subscription."""
    customer_id = data.get("customer")
    result = await db.execute(
        select(Business).where(Business.stripe_customer_id == customer_id)
    )
    business = result.scalar_one_or_none()

    if business:
        business.subscription_status = data.get("status")
        if data.get("trial_end"):
            business.trial_ends_at = datetime.fromtimestamp(data["trial_end"])
        await db.commit()


async def handle_subscription_updated(data: Dict[str, Any], db: AsyncSession):
    """Handle subscription update (plan change, etc)."""
    customer_id = data.get("customer")
    result = await db.execute(
        select(Business).where(Business.stripe_customer_id == customer_id)
    )
    business = result.scalar_one_or_none()

    if business:
        business.subscription_status = data.get("status")

        # Check for plan change
        items = data.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
            # Reverse lookup plan from price ID
            for plan, pid in config.STRIPE_PRICES.items():
                if pid == price_id:
                    business.subscription_plan = plan
                    break

        await db.commit()


async def handle_subscription_deleted(data: Dict[str, Any], db: AsyncSession):
    """Handle subscription cancellation."""
    customer_id = data.get("customer")
    result = await db.execute(
        select(Business).where(Business.stripe_customer_id == customer_id)
    )
    business = result.scalar_one_or_none()

    if business:
        business.subscription_status = "cancelled"
        await db.commit()


async def handle_payment_succeeded(data: Dict[str, Any], db: AsyncSession):
    """Handle successful payment."""
    customer_id = data.get("customer")
    result = await db.execute(
        select(Business).where(Business.stripe_customer_id == customer_id)
    )
    business = result.scalar_one_or_none()

    if business:
        business.subscription_status = "active"
        await db.commit()


async def handle_payment_failed(data: Dict[str, Any], db: AsyncSession):
    """Handle failed payment."""
    customer_id = data.get("customer")
    result = await db.execute(
        select(Business).where(Business.stripe_customer_id == customer_id)
    )
    business = result.scalar_one_or_none()

    if business:
        business.subscription_status = "past_due"
        await db.commit()


@router.post("/vapi")
async def vapi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle Vapi webhook events (call events, transcripts).
    """
    data = await request.json()
    message_type = data.get("message", {}).get("type")

    if message_type == "end-of-call-report":
        await handle_call_ended(data, db)
    elif message_type == "transcript":
        await handle_transcript_update(data, db)
    elif message_type == "function-call":
        return await handle_function_call(data, db)

    return {"received": True}


async def handle_call_ended(data: Dict[str, Any], db: AsyncSession):
    """Handle end of call report from Vapi."""
    message = data.get("message", {})
    call_data = message.get("call", {})

    assistant_id = call_data.get("assistantId")

    # Find business by assistant ID
    result = await db.execute(
        select(Business).where(Business.vapi_assistant_id == assistant_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        return

    # Extract call details
    vapi_call_id = call_data.get("id")
    caller_phone = call_data.get("customer", {}).get("number", "Unknown")

    # Check for existing call record
    existing = await db.execute(
        select(Call).where(Call.vapi_call_id == vapi_call_id)
    )
    call = existing.scalar_one_or_none()

    # Get transcript and summary
    transcript = message.get("transcript", "")
    summary = message.get("summary", "")
    recording_url = message.get("recordingUrl")
    duration = message.get("endedReason", {})

    # Calculate duration from timestamps
    started_at = call_data.get("startedAt")
    ended_at = call_data.get("endedAt")
    duration_seconds = None
    if started_at and ended_at:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
        duration_seconds = int((end - start).total_seconds())

    # Determine if appointment was booked (check for booking in transcript)
    appointment_booked = any(
        phrase in transcript.lower()
        for phrase in ["appointment confirmed", "booked you for", "scheduled for", "see you on"]
    )

    if call:
        # Update existing call
        call.transcript = transcript
        call.summary = summary
        call.recording_url = recording_url
        call.duration_seconds = duration_seconds
        call.status = "completed"
        call.appointment_booked = appointment_booked
    else:
        # Create new call record
        call = Call(
            id=uuid4(),
            business_id=business.id,
            vapi_call_id=vapi_call_id,
            caller_phone=caller_phone,
            status="completed",
            duration_seconds=duration_seconds,
            transcript=transcript,
            summary=summary,
            recording_url=recording_url,
            appointment_booked=appointment_booked
        )
        db.add(call)

    # Record usage
    usage_record = UsageRecord(
        id=uuid4(),
        business_id=business.id,
        record_date=datetime.utcnow().date(),
        call_count=1,
        call_minutes=round((duration_seconds or 0) / 60, 2)
    )
    db.add(usage_record)

    await db.commit()

    # Send email notification
    email = EmailService()
    if business.email:
        await email.send_call_notification(
            email=business.email,
            business_name=business.name,
            caller_name=call.caller_name,
            caller_phone=caller_phone,
            summary=summary,
            appointment_booked=appointment_booked
        )


async def handle_transcript_update(data: Dict[str, Any], db: AsyncSession):
    """Handle real-time transcript updates."""
    # For now, we just wait for end-of-call-report
    pass


async def handle_function_call(data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """
    Handle Vapi function calls (book appointment, etc).
    Returns response to Vapi.
    """
    message = data.get("message", {})
    function_call = message.get("functionCall", {})
    function_name = function_call.get("name")
    parameters = function_call.get("parameters", {})

    call_data = message.get("call", {})
    assistant_id = call_data.get("assistantId")

    # Find business
    result = await db.execute(
        select(Business).where(Business.vapi_assistant_id == assistant_id)
    )
    business = result.scalar_one_or_none()

    if not business:
        return {"result": "Error: Business not found"}

    if function_name == "bookAppointment":
        # Create appointment
        appointment = Appointment(
            id=uuid4(),
            business_id=business.id,
            customer_name=parameters.get("customerName", "Unknown"),
            customer_phone=parameters.get("customerPhone", ""),
            customer_email=parameters.get("customerEmail"),
            service_type=parameters.get("serviceType", "General"),
            appointment_date=datetime.strptime(
                parameters.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
                "%Y-%m-%d"
            ).date(),
            appointment_time=parameters.get("time", "9:00 AM"),
            status="scheduled",
            notes=parameters.get("notes")
        )
        db.add(appointment)
        await db.commit()

        # Send confirmation email if we have customer email
        if appointment.customer_email:
            email = EmailService()
            await email.send_appointment_confirmation(
                customer_email=appointment.customer_email,
                business_name=business.name,
                customer_name=appointment.customer_name,
                service_type=appointment.service_type,
                appointment_date=appointment.appointment_date.strftime("%B %d, %Y"),
                appointment_time=appointment.appointment_time,
                address=business.address
            )

        return {
            "result": f"Appointment booked for {appointment.customer_name} on {appointment.appointment_date} at {appointment.appointment_time}"
        }

    elif function_name == "checkAvailability":
        # For now, return that we have availability
        return {
            "result": "Available times: 9am, 10am, 11am, 2pm, 3pm, 4pm"
        }

    elif function_name == "getBusinessInfo":
        return {
            "result": {
                "name": business.name,
                "hours": business.business_hours,
                "services": business.services,
                "address": business.address
            }
        }

    return {"result": "Function not recognized"}
