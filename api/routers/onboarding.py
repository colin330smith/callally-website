"""
Onboarding Router - 5-step business setup
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Dict, Any

from database.connection import get_db
from database.models import User, Business
from services.vapi_service import VapiService
from services.stripe_service import StripeService
from services.email_service import EmailService
from middleware.auth_middleware import get_current_user
from schemas.business import (
    OnboardingStepRequest,
    BusinessResponse,
    OnboardingCompleteResponse
)

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


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


def apply_step_data(business: Business, step: int, data: Dict[str, Any]):
    """Apply onboarding step data to business model."""

    if step == 1:
        # Business basics
        business.name = data.get("business_name", business.name)
        business.industry = data.get("industry")
        business.phone = data.get("phone")
        business.service_area = data.get("service_area")

    elif step == 2:
        # Services
        business.services = data.get("services", [])
        business.custom_services = data.get("custom_services")
        business.appointment_types = data.get("appointment_types", [])
        business.business_hours = data.get("business_hours", {})

    elif step == 3:
        # Call handling
        business.call_mode = data.get("call_mode", "forwarding")
        business.rings_before_ai = data.get("rings_before_ai", 3)
        business.emergency_dispatch = data.get("emergency_dispatch", False)
        business.emergency_phones = data.get("emergency_phones", [])
        business.emergency_keywords = data.get("emergency_keywords", [])

    elif step == 4:
        # AI Agent customization
        business.agent_name = data.get("agent_name", "Alex")
        business.agent_voice = data.get("agent_voice", "rachel")

    elif step == 5:
        # Notifications
        business.notification_email = data.get("notification_email")
        business.notification_phone = data.get("notification_phone")


@router.post("/{business_id}/step", response_model=BusinessResponse)
async def save_onboarding_step(
    business_id: UUID,
    request: OnboardingStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save data for an onboarding step.
    """
    business = await get_business_for_user(business_id, current_user, db)

    if business.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Onboarding already complete"
        )

    # Apply the step data
    apply_step_data(business, request.step, request.data)

    # Update step counter if moving forward
    if request.step >= business.onboarding_step:
        business.onboarding_step = request.step + 1

    await db.commit()
    await db.refresh(business)

    return BusinessResponse.model_validate(business)


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_onboarding_status(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current onboarding status and saved data.
    """
    business = await get_business_for_user(business_id, current_user, db)
    return BusinessResponse.model_validate(business)


@router.post("/{business_id}/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete onboarding: Create Vapi assistant, provision phone, start trial.
    """
    import traceback

    business = await get_business_for_user(business_id, current_user, db)

    if business.status == "active":
        return OnboardingCompleteResponse(
            success=True,
            business_id=business.id,
            phone_number=business.vapi_phone_number,
            assistant_id=business.vapi_assistant_id,
            message="Onboarding already complete"
        )

    # Validate minimum required data
    if not business.name or not business.industry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete all onboarding steps first"
        )

    vapi = VapiService()
    stripe = StripeService()
    email = EmailService()

    errors = []

    # 1. Create Vapi AI Assistant
    try:
        assistant_id = await vapi.create_assistant(business)
        if assistant_id:
            business.vapi_assistant_id = assistant_id
        else:
            errors.append("Vapi assistant creation returned None")
    except Exception as e:
        errors.append(f"Vapi assistant error: {str(e)}")
        print(f"Vapi error traceback: {traceback.format_exc()}")
        assistant_id = None

    # 2. Provision phone number (only if assistant was created)
    if business.vapi_assistant_id:
        try:
            phone_result = await vapi.provision_phone_number(business.vapi_assistant_id)
            if phone_result:
                business.vapi_phone_id = phone_result["phone_id"]
                business.vapi_phone_number = phone_result.get("phone_number")
                # If no phone number returned, note that it needs manual setup
                if not business.vapi_phone_number:
                    print(f"Phone created without number - manual setup needed for business {business.id}")
        except Exception as e:
            # Phone provisioning is optional - assistant still works
            print(f"Phone provisioning note: {str(e)}")

    # 3. Create Stripe customer
    try:
        stripe_customer_id = await stripe.create_customer(
            email=business.notification_email or current_user.email,
            business_name=business.name,
            business_id=str(business.id)
        )

        if stripe_customer_id:
            business.stripe_customer_id = stripe_customer_id

            # 4. Create trial subscription
            try:
                subscription = await stripe.create_subscription(
                    customer_id=stripe_customer_id,
                    plan="starter",
                    trial_days=7
                )

                if subscription:
                    business.subscription_plan = "starter"
                    business.subscription_status = subscription["status"]
                    business.trial_ends_at = subscription["trial_end"]
                else:
                    errors.append("Subscription creation returned None (price ID may not be set)")
            except Exception as e:
                errors.append(f"Subscription error: {str(e)}")
        else:
            errors.append("Stripe customer creation returned None")
    except Exception as e:
        errors.append(f"Stripe error: {str(e)}")
        print(f"Stripe error traceback: {traceback.format_exc()}")

    # Mark onboarding complete even with partial failures
    business.status = "active"
    await db.commit()

    # 5. Send welcome email
    if business.notification_email:
        try:
            await email.send_welcome_email(
                email=business.notification_email,
                business_name=business.name,
                phone_number=business.vapi_phone_number or "Pending"
            )
        except Exception as e:
            errors.append(f"Email error: {str(e)}")

    # Build response message
    if errors:
        print(f"Onboarding completed with errors: {errors}")
        message = "Setup complete with some issues: " + "; ".join(errors[:2])
    else:
        message = "Your AI receptionist is now live!"

    return OnboardingCompleteResponse(
        success=True,
        business_id=business.id,
        phone_number=business.vapi_phone_number,
        assistant_id=business.vapi_assistant_id,
        message=message
    )
