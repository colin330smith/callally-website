"""
CallAlly Sales Engine - AI Cold Calling System
================================================
Automated outbound calls using Vapi AI voice agents.
"""

import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
import config
import database

# Vapi cold call script
COLD_CALL_SCRIPT = """
You are a friendly sales representative for CallAlly, an AI-powered call answering service for service businesses.

## Your Goal
Get the business owner interested in a free 7-day trial of CallAlly.

## Key Value Props (use conversationally, not as a script)
- AI answers their calls 24/7 when they can't
- Sounds remarkably human - callers don't know it's AI
- Books appointments directly into their calendar
- Texts them lead details immediately
- $99/month after trial - one job pays for months
- 10 minutes to set up

## Opening
"Hey, is this [owner_name]? Great! This is Colin from CallAlly. I'll be super quick - I know you're busy."

"Quick question - when you're on a job, who's answering your phone?"

## Listen for pain
- If they say "voicemail" or "we miss calls" → emphasize 24/7 coverage
- If they mention staff issues → emphasize reliability, no sick days
- If they're skeptical about AI → offer the free trial to try it themselves

## Handle objections

"We already have a receptionist"
→ "That's great! What happens after 5pm or on weekends? That's when 40% of calls come in. We can back them up."

"AI won't sound natural"
→ "I totally get that concern. That's why we offer a 7-day trial - call your own number and see. Most people can't tell."

"We don't miss that many calls"
→ "You'd be surprised. Most businesses miss 5-10 calls a day. At $300+ per job, that adds up fast. Want me to set you up with a trial to find out?"

"What's the cost?"
→ "$99/month for most businesses. But here's the thing - one captured job pays for months. And the first 7 days are free."

"I need to think about it"
→ "Totally fair. How about I set you up with the free trial right now? No credit card, no commitment. If you love it, keep it. If not, no worries."

## Closing
Always try to get them to:
1. Start the free trial (primary goal)
2. Visit callallynow.com/signup
3. Schedule a callback if busy

"Can I get your email to send over the trial link? It takes 10 minutes to set up."

## Tone
- Confident but not pushy
- Empathetic to their business challenges
- Quick and respectful of their time
- Authentic, not salesy

## Business Context
Business: {business_name}
Vertical: {vertical}
City: {city}, {state}
Owner Name: {owner_name}
"""

class AICaller:
    """AI-powered cold calling system using Vapi."""

    def __init__(self):
        self.api_key = config.VAPI_API_KEY
        self.assistant_id = config.VAPI_ASSISTANT_ID
        self.base_url = "https://api.vapi.ai"

    def create_assistant(self, name: str = "CallAlly Sales Agent") -> Optional[str]:
        """Create a Vapi assistant for cold calling."""
        if not self.api_key:
            print("Vapi API key not configured")
            return None

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            "name": name,
            "model": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "systemPrompt": COLD_CALL_SCRIPT
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "pNInz6obpgDQGcFmaJgB",  # Adam - friendly male voice
                "stability": 0.5,
                "similarityBoost": 0.75
            },
            "firstMessage": "Hey, is this the owner? Great! This is Colin from CallAlly. I'll be super quick - I know you're busy.",
            "endCallMessage": "Thanks for your time! Have a great day.",
            "recordingEnabled": True,
            "transcriptionEnabled": True,
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 300,  # 5 min max
            "backgroundSound": "office",
        }

        try:
            response = requests.post(
                f"{self.base_url}/assistant",
                headers=headers,
                json=payload
            )
            if response.status_code == 201:
                assistant_id = response.json().get('id')
                print(f"Created assistant: {assistant_id}")
                return assistant_id
            else:
                print(f"Error creating assistant: {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def make_call(self, lead: Dict) -> Dict:
        """Make an outbound call to a lead."""
        if not self.api_key:
            return {'success': False, 'error': 'API key not configured'}

        if not lead.get('phone'):
            return {'success': False, 'error': 'No phone number'}

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Personalize the script
        personalized_script = COLD_CALL_SCRIPT.format(
            business_name=lead.get('business_name', 'your business'),
            vertical=lead.get('vertical', 'service'),
            city=lead.get('city', ''),
            state=lead.get('state', ''),
            owner_name=lead.get('owner_name', 'there')
        )

        payload = {
            "assistantId": self.assistant_id,
            "assistantOverrides": {
                "model": {
                    "systemPrompt": personalized_script
                },
                "firstMessage": f"Hey, is this {lead.get('owner_name', 'the owner')}? Great! This is Colin from CallAlly. I'll be super quick."
            },
            "customer": {
                "number": lead['phone'],
                "name": lead.get('owner_name')
            },
            "phoneNumberId": config.VAPI_PHONE_ID if hasattr(config, 'VAPI_PHONE_ID') else None
        }

        try:
            response = requests.post(
                f"{self.base_url}/call/phone",
                headers=headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                call_data = response.json()
                database.log_outreach(
                    lead['id'], 'call',
                    subject=f"Cold call to {lead['business_name']}",
                    content=personalized_script[:500],
                    status='initiated'
                )
                return {
                    'success': True,
                    'call_id': call_data.get('id'),
                    'status': call_data.get('status')
                }
            else:
                error = response.text
                database.log_outreach(lead['id'], 'call', status='failed', error=error)
                return {'success': False, 'error': error}

        except Exception as e:
            database.log_outreach(lead['id'], 'call', status='error', error=str(e))
            return {'success': False, 'error': str(e)}

    def get_call_result(self, call_id: str) -> Dict:
        """Get the result/transcript of a completed call."""
        headers = {'Authorization': f'Bearer {self.api_key}'}

        try:
            response = requests.get(
                f"{self.base_url}/call/{call_id}",
                headers=headers
            )
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def run_calling_campaign(self, leads: List[Dict], delay_minutes: int = 2) -> Dict:
        """Run a batch of outbound calls."""
        results = {
            'initiated': 0,
            'failed': 0,
            'calls': []
        }

        for lead in leads:
            result = self.make_call(lead)

            if result.get('success'):
                results['initiated'] += 1
                results['calls'].append({
                    'lead_id': lead['id'],
                    'business': lead['business_name'],
                    'call_id': result.get('call_id')
                })
                print(f"✓ Calling {lead['business_name']} - {lead['phone']}")
            else:
                results['failed'] += 1
                print(f"✗ Failed: {lead['business_name']} - {result.get('error')}")

            # Space out calls
            time.sleep(delay_minutes * 60)

        return results

def run_calling_campaign(limit: int = None):
    """Run daily calling campaign."""
    limit = limit or config.DAILY_CALL_LIMIT
    caller = AICaller()

    print(f"\n{'='*50}")
    print(f"CallAlly AI Calling Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Get leads for calling
    leads = database.get_leads_for_outreach(limit, 'call')
    print(f"Found {len(leads)} leads for calling\n")

    if not leads:
        print("No leads ready for calls.")
        return

    # Make calls
    results = caller.run_calling_campaign(leads)

    print(f"\n{'='*50}")
    print(f"Results: {results['initiated']} calls initiated, {results['failed']} failed")
    print(f"{'='*50}\n")

    return results

if __name__ == "__main__":
    # Test with 3 calls
    run_calling_campaign(limit=3)
