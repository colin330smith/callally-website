"""
Stripe Service - Subscription and billing management
"""
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import config

stripe.api_key = config.STRIPE_SECRET_KEY


class StripeService:
    """Manage Stripe customers, subscriptions, and billing."""

    @staticmethod
    async def create_customer(email: str, business_name: str, business_id: str) -> Optional[str]:
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=business_name,
                metadata={
                    "business_id": str(business_id)
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            print(f"Stripe customer error: {e}")
            return None

    @staticmethod
    async def create_subscription(
        customer_id: str,
        plan: str = "starter",
        trial_days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """Create a subscription with a trial period."""
        price_id = config.STRIPE_PRICES.get(plan)
        if not price_id:
            print(f"No price ID configured for plan: {plan}")
            # Still return a valid response for trial-only mode
            return {
                "subscription_id": None,
                "status": "trialing",
                "trial_end": datetime.utcnow() + timedelta(days=trial_days),
                "client_secret": None
            }

        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                trial_period_days=trial_days,
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"]
            )

            # Safely get client_secret
            client_secret = None
            if subscription.latest_invoice and hasattr(subscription.latest_invoice, 'payment_intent'):
                if subscription.latest_invoice.payment_intent:
                    client_secret = subscription.latest_invoice.payment_intent.client_secret

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                "client_secret": client_secret
            }
        except stripe.error.StripeError as e:
            print(f"Stripe subscription error: {e}")
            return None

    @staticmethod
    async def create_checkout_session(
        customer_id: str,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Optional[str]:
        """Create a Stripe Checkout session."""
        price_id = config.STRIPE_PRICES.get(plan)
        if not price_id:
            return None

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    "trial_period_days": 7
                }
            )
            return session.url
        except stripe.error.StripeError as e:
            print(f"Stripe checkout error: {e}")
            return None

    @staticmethod
    async def create_portal_session(customer_id: str, return_url: str) -> Optional[str]:
        """Create a Stripe Customer Portal session."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
        except stripe.error.StripeError as e:
            print(f"Stripe portal error: {e}")
            return None

    @staticmethod
    async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel a subscription."""
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.delete(subscription_id)
            return True
        except stripe.error.StripeError as e:
            print(f"Stripe cancel error: {e}")
            return False

    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
        """Verify and construct webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                config.STRIPE_WEBHOOK_SECRET
            )
            return event
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            print(f"Stripe webhook verification error: {e}")
            return None
