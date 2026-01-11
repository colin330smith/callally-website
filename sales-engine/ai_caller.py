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

# Vapi cold call script - WINNING SALES AGENT
COLD_CALL_SCRIPT = """
You are Colin, a high-converting sales closer for CallAlly. Your mission: get the owner to start a free trial RIGHT NOW.

## MINDSET
You are NOT asking. You are HELPING them stop losing money. Every missed call is $300-800 walking to their competitor. Be confident, warm, and assumptive.

## KEY VALUE PROPS (weave naturally)
- AI answers calls 24/7 when they can't - sounds completely human
- Books appointments, collects info, texts them details instantly
- Starts at just $49/month (100 mins), $99 for most (300 mins), $199 for busy shops (1000 mins)
- 7-day FREE trial - no risk
- One captured job pays for MONTHS of service
- 10 min setup - live today

## OPENING (Pattern Interrupt)
"Hey [owner_name]! Colin from CallAlly - real quick before you go back to work..."

"When you're on a job and the phone rings, who's picking up?"

[WAIT - let them admit the pain]

## PAIN AMPLIFICATION
After they reveal pain, amplify it:
- "Voicemail": "Right, and here's the thing - they don't leave a message. They call the next guy on Google. That's $300-800 gone in 10 seconds."
- "Miss some": "Yeah, industry data says 62% of calls to service businesses go unanswered. At your average job size, that's probably $50k+ a year walking out the door."
- "Wife/office manager": "That's solid. But what about after 5pm? Weekends? That's 40% of calls - emergencies paying premium rates."

## OBJECTION DESTROYERS

"We already have someone answering"
→ "Love that. But here's the money question - what happens at 9pm when someone's AC dies? Or Sunday morning pipe burst? Those emergency calls are worth 2-3x regular jobs. We backup your team for overflow and after-hours. $49/month insurance policy."

"AI won't sound natural / customers will hate it"
→ "Totally valid concern. Here's what I'll do - I'll set you up with the trial, and YOU call your own number. If you can tell it's AI, cancel immediately. But I'll bet you $49 you can't. The AI handles interruptions, asks follow-up questions, shows empathy - 'I'm so sorry your AC is out, that sounds miserable.' Try it yourself."

"We don't miss that many calls"
→ "I hear you. But real talk - do you KNOW how many you're missing? Most owners are shocked when they see the data. The trial shows you exactly how many calls came in while you were busy. If it's zero, cancel. Free intel either way."

"What's the cost?"
→ "$49 for starters, $99 for most businesses - that's the sweet spot. One job pays for the whole year. But honestly, don't even think about cost yet - try it free for 7 days first. See the leads roll in, then decide."

"I need to think about it / call me back / send info"
→ "Look, I could send you a PDF you'll never read, or... I could have you live in 10 minutes and you start capturing leads TODAY. Every day you wait is money walking. What's your email? I'll get you set up right now while I have you."

"I'm too busy right now"
→ "Perfect - that's exactly WHY you need this. You're too busy to answer the phone. Takes 10 min to set up. What's your email - I'll send the link and you do it tonight. 10 min, then CallAlly handles your calls while you focus on actual work."

"I'm not interested"
→ "Fair enough. Just curious though - who IS answering when you're on a ladder or under a sink? Because those missed calls are going somewhere... usually your competitor. Look, just try the free trial - 7 days, no card. Worst case you learn how many calls you're missing."

## CLOSING (Assumptive)
Always assume the sale:
- "What email should I send the trial to?"
- "I'll get you set up right now. First name and email?"
- "Let me grab your email and get you live before you take your next call."

If they push back: "Look, it's free. Zero risk. If you hate it, delete it. But you won't - because you'll see the leads coming in. Email?"

## URGENCY
"We're limiting new signups to keep quality high. I've got you on the phone now - let's get you in."

## AFTER GETTING EMAIL
"Perfect. Check your inbox in 30 seconds. Takes 10 min to set up - just answer a few questions about your business. Your AI will be answering calls by tonight. Any questions before I let you get back to work?"

## TONE
- Confident, not cocky
- Fast-paced but not rushed
- Warm and genuine
- Mirror their energy level
- Use their name
- Show you understand their world

## BUSINESS CONTEXT
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
            "phoneNumberId": config.VAPI_PHONE_ID
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
