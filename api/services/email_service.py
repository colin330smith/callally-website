"""
Email Service - Transactional emails via Resend
"""
import httpx
from typing import Optional, Dict, Any

import config


class EmailService:
    """Send transactional emails via Resend."""

    BASE_URL = "https://api.resend.com"

    def __init__(self):
        self.api_key = config.RESEND_API_KEY
        self.from_email = config.FROM_EMAIL

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> bool:
        """Send an email."""
        if not self.api_key:
            print("Resend API key not configured")
            return False

        payload = {
            "from": self.from_email,
            "to": [to],
            "subject": subject,
            "html": html
        }
        if text:
            payload["text"] = text

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/emails",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Email send error: {e}")
                return False

    async def send_welcome_email(self, email: str, business_name: str, phone_number: str) -> bool:
        """Send welcome email after onboarding completion."""
        subject = f"Welcome to CallAlly - Your AI Receptionist is Live!"

        html = f"""
        <div style="font-family: 'DM Sans', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 40px;">
                <div style="display: inline-block; background: #0f172a; padding: 12px; border-radius: 12px;">
                    <span style="color: #fbbf24; font-size: 24px;">&#9742;</span>
                </div>
                <h1 style="margin: 16px 0 0; color: #0f172a;">CallAlly</h1>
            </div>

            <h2 style="color: #0f172a; margin-bottom: 16px;">Your AI Receptionist is Live! &#127881;</h2>

            <p style="color: #475569; line-height: 1.6;">
                Congratulations, <strong>{business_name}</strong>! Your AI receptionist is now answering calls 24/7.
            </p>

            <div style="background: #fef3c7; border-radius: 12px; padding: 24px; margin: 24px 0;">
                <p style="margin: 0 0 8px; color: #92400e; font-weight: 600;">Your New Phone Number</p>
                <p style="margin: 0; font-size: 24px; font-weight: 700; color: #0f172a;">{phone_number}</p>
            </div>

            <h3 style="color: #0f172a; margin: 32px 0 16px;">What happens now?</h3>

            <ol style="color: #475569; line-height: 1.8; padding-left: 20px;">
                <li><strong>Test your AI:</strong> Call your new number to hear your AI in action</li>
                <li><strong>Forward your calls:</strong> Set up call forwarding from your main number</li>
                <li><strong>Check your dashboard:</strong> See call transcripts and appointments in real-time</li>
            </ol>

            <div style="text-align: center; margin: 40px 0;">
                <a href="{config.BASE_URL}/dashboard.html" style="display: inline-block; background: #f59e0b; color: #0f172a; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600;">
                    View Your Dashboard
                </a>
            </div>

            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 40px 0;">

            <p style="color: #64748b; font-size: 14px; text-align: center;">
                Questions? Reply to this email or call us at (650) 201-5786<br>
                <a href="{config.BASE_URL}" style="color: #f59e0b;">callallynow.com</a>
            </p>
        </div>
        """

        return await self.send_email(email, subject, html)

    async def send_call_notification(
        self,
        email: str,
        business_name: str,
        caller_name: str,
        caller_phone: str,
        summary: str,
        appointment_booked: bool
    ) -> bool:
        """Send notification after a call."""
        subject = f"New Call: {caller_name or caller_phone} - {business_name}"

        appointment_badge = ""
        if appointment_booked:
            appointment_badge = '<span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 100px; font-size: 12px; font-weight: 600;">APPOINTMENT BOOKED</span>'

        html = f"""
        <div style="font-family: 'DM Sans', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <h2 style="color: #0f172a; margin: 0 0 16px;">New Call Received {appointment_badge}</h2>

            <div style="background: #f8fafc; border-radius: 12px; padding: 24px; margin: 24px 0;">
                <p style="margin: 0 0 8px; color: #64748b; font-size: 14px;">Caller</p>
                <p style="margin: 0 0 16px; font-size: 18px; font-weight: 600; color: #0f172a;">{caller_name or 'Unknown'}</p>

                <p style="margin: 0 0 8px; color: #64748b; font-size: 14px;">Phone</p>
                <p style="margin: 0; font-size: 18px; color: #0f172a;">
                    <a href="tel:{caller_phone}" style="color: #0f172a; text-decoration: none;">{caller_phone}</a>
                </p>
            </div>

            <h3 style="color: #0f172a; margin: 24px 0 12px;">Call Summary</h3>
            <p style="color: #475569; line-height: 1.6; background: #f8fafc; padding: 16px; border-radius: 8px;">
                {summary or 'No summary available'}
            </p>

            <div style="text-align: center; margin: 32px 0;">
                <a href="{config.BASE_URL}/dashboard.html" style="display: inline-block; background: #0f172a; color: #fbbf24; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600;">
                    View Full Transcript
                </a>
            </div>
        </div>
        """

        return await self.send_email(email, subject, html)

    async def send_appointment_confirmation(
        self,
        customer_email: str,
        business_name: str,
        customer_name: str,
        service_type: str,
        appointment_date: str,
        appointment_time: str,
        address: Optional[str] = None
    ) -> bool:
        """Send appointment confirmation to customer."""
        subject = f"Appointment Confirmed - {business_name}"

        address_section = ""
        if address:
            address_section = f"""
            <p style="margin: 0 0 8px; color: #64748b; font-size: 14px;">Address</p>
            <p style="margin: 0 0 16px; color: #0f172a;">{address}</p>
            """

        html = f"""
        <div style="font-family: 'DM Sans', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <h2 style="color: #0f172a; margin: 0 0 8px;">Appointment Confirmed &#9989;</h2>
            <p style="color: #64748b; margin: 0 0 32px;">Hi {customer_name}, your appointment is confirmed!</p>

            <div style="background: #f8fafc; border-radius: 12px; padding: 24px; margin: 24px 0;">
                <p style="margin: 0 0 8px; color: #64748b; font-size: 14px;">Service</p>
                <p style="margin: 0 0 16px; font-size: 18px; font-weight: 600; color: #0f172a;">{service_type}</p>

                <p style="margin: 0 0 8px; color: #64748b; font-size: 14px;">Date & Time</p>
                <p style="margin: 0 0 16px; font-size: 18px; color: #0f172a;">{appointment_date} at {appointment_time}</p>

                {address_section}

                <p style="margin: 0 0 8px; color: #64748b; font-size: 14px;">Business</p>
                <p style="margin: 0; color: #0f172a;">{business_name}</p>
            </div>

            <p style="color: #64748b; line-height: 1.6;">
                Need to reschedule? Please call us at least 24 hours before your appointment.
            </p>
        </div>
        """

        return await self.send_email(customer_email, subject, html)
