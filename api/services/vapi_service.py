"""
Vapi AI Service - Create and manage AI assistants
"""
import httpx
from typing import Optional, Dict, Any

import config
from database.models import Business


# AI Receptionist prompt template
RECEPTIONIST_PROMPT = """
You are {agent_name}, a friendly and professional AI receptionist for {business_name}.

## ABOUT THE BUSINESS
- Industry: {industry}
- Services offered: {services}
- Service area: {service_area}
- Business hours: {business_hours}

## YOUR ROLE
1. Answer calls professionally and warmly
2. Collect caller information (name, phone, address if needed)
3. Understand their needs
4. Book appointments when appropriate
5. Handle emergencies according to protocol

## GREETING
"Hi, thanks for calling {business_name}! This is {agent_name}, how can I help you today?"

## APPOINTMENT BOOKING
When a caller wants to schedule service:
1. Confirm what service they need
2. Get their name and callback number
3. Ask for their address (for service calls)
4. Suggest available times
5. Confirm the appointment details
6. Let them know someone will confirm the appointment

Available appointment types: {appointment_types}

## COLLECTING INFORMATION
Always try to collect:
- Caller's full name
- Phone number (confirm it)
- Address (for service calls)
- Brief description of what they need
- Best time to reach them

## EMERGENCY HANDLING
{emergency_instructions}

## WHEN YOU CAN'T HELP
If you can't answer a question or help with something:
1. Apologize politely
2. Offer to have someone call them back
3. Get their callback number
4. Note what they need help with

## TONE & STYLE
- Warm and friendly, like talking to a helpful neighbor
- Professional but not stiff
- Patient with questions
- Speak naturally, not like a robot
- Use the caller's name once you know it
- Mirror their energy level

## IMPORTANT RULES
- Be transparent that you're an AI assistant
- Never make promises you can't keep
- Don't discuss pricing specifics - say "I'll have someone get you a quote"
- If they're frustrated, show empathy: "I completely understand, that sounds frustrating"
- Always end calls positively: "Is there anything else I can help with today?"
"""

VOICE_OPTIONS = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",  # Rachel - female, friendly
    "adam": "pNInz6obpgDQGcFmaJgB",    # Adam - male, professional
    "sarah": "EXAVITQu4vr4xnSDxMaL",   # Sarah - female, warm
    "josh": "TxGEqnHWrfWFTfGW9XjX",    # Josh - male, casual
}


class VapiService:
    """Manage Vapi AI assistants and calls."""

    BASE_URL = "https://api.vapi.ai"

    def __init__(self):
        self.api_key = config.VAPI_API_KEY

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_system_prompt(self, business: Business) -> str:
        """Build a customized system prompt for the business."""
        # Format services
        services_list = ", ".join(business.services or [])
        if business.custom_services:
            services_list += f", {business.custom_services}"

        # Format business hours
        hours = business.business_hours or {}
        hours_str = f"Weekdays: {hours.get('weekday', 'Not specified')}, Weekends: {hours.get('weekend', 'Closed')}"

        # Format appointment types
        appt_types = ", ".join(business.appointment_types or ["general appointment"])

        # Build emergency instructions
        if business.emergency_dispatch and business.emergency_keywords:
            keywords = ", ".join(business.emergency_keywords)
            phones = ", ".join(business.emergency_phones or [])
            emergency_instructions = f"""
If the caller mentions any of these emergency keywords: {keywords}
1. Express concern and urgency
2. Tell them you're connecting them to an on-call technician immediately
3. Get their phone number and address if you don't have it
4. Note: Emergency contacts are: {phones}
"""
        else:
            emergency_instructions = """
For urgent situations:
1. Express understanding of the urgency
2. Get their phone number
3. Let them know someone will call them back as soon as possible
4. Note what's happening so the team can prioritize
"""

        return RECEPTIONIST_PROMPT.format(
            agent_name=business.agent_name or "Alex",
            business_name=business.name,
            industry=business.industry or "service",
            services=services_list or "various services",
            service_area=business.service_area or "local area",
            business_hours=hours_str,
            appointment_types=appt_types,
            emergency_instructions=emergency_instructions
        )

    async def create_assistant(self, business: Business) -> Optional[str]:
        """Create a Vapi assistant for the business."""
        if not self.api_key:
            return None

        system_prompt = self._build_system_prompt(business)
        voice_id = VOICE_OPTIONS.get(business.agent_voice, VOICE_OPTIONS["rachel"])

        payload = {
            "name": f"{business.name} - AI Receptionist",
            "model": {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "systemPrompt": system_prompt
            },
            "voice": {
                "provider": "11labs",
                "voiceId": voice_id,
                "stability": 0.5,
                "similarityBoost": 0.75
            },
            "firstMessage": f"Hi, thanks for calling {business.name}! This is {business.agent_name or 'Alex'}, how can I help you today?",
            "endCallMessage": "Thanks for calling! Have a great day!",
            "recordingEnabled": True,
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 600,  # 10 minutes max
            "backgroundSound": "office",
            "serverUrl": f"{config.API_URL}/api/webhooks/vapi"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/assistant",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                if response.status_code == 201:
                    data = response.json()
                    return data.get("id")
                else:
                    print(f"Vapi error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"Vapi request error: {e}")
                return None

    async def update_assistant(self, assistant_id: str, business: Business) -> bool:
        """Update an existing assistant with new business settings."""
        if not self.api_key or not assistant_id:
            return False

        system_prompt = self._build_system_prompt(business)
        voice_id = VOICE_OPTIONS.get(business.agent_voice, VOICE_OPTIONS["rachel"])

        payload = {
            "name": f"{business.name} - AI Receptionist",
            "model": {
                "systemPrompt": system_prompt
            },
            "voice": {
                "voiceId": voice_id
            },
            "firstMessage": f"Hi, thanks for calling {business.name}! This is {business.agent_name or 'Alex'}, how can I help you today?"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.BASE_URL}/assistant/{assistant_id}",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                return response.status_code == 200
            except Exception as e:
                print(f"Vapi update error: {e}")
                return False

    async def provision_phone_number(self, assistant_id: str) -> Optional[Dict[str, str]]:
        """Purchase and assign a phone number to the assistant."""
        if not self.api_key or not assistant_id:
            return None

        # First, buy a phone number
        buy_payload = {
            "provider": "twilio",
            "areaCode": "415",  # San Francisco area code
            "assistantId": assistant_id
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/phone-number",
                    headers=self._get_headers(),
                    json=buy_payload,
                    timeout=30.0
                )
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "phone_id": data.get("id"),
                        "phone_number": data.get("number")
                    }
                else:
                    print(f"Vapi phone error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"Vapi phone request error: {e}")
                return None

    async def make_test_call(self, assistant_id: str, phone_number: str, phone_id: str) -> Optional[str]:
        """Initiate an outbound test call."""
        if not self.api_key or not assistant_id:
            return None

        payload = {
            "assistantId": assistant_id,
            "customer": {
                "number": phone_number
            },
            "phoneNumberId": phone_id
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/call/phone",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                if response.status_code in [200, 201]:
                    data = response.json()
                    return data.get("id")
                else:
                    print(f"Vapi call error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"Vapi call request error: {e}")
                return None

    async def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a call including transcript and recording."""
        if not self.api_key or not call_id:
            return None

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/call/{call_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"Vapi get call error: {e}")
                return None
