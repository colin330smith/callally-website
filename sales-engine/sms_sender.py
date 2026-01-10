"""
CallAlly Sales Engine - SMS Outreach System
=============================================
Automated SMS outreach using Twilio.
"""

import time
from datetime import datetime
from typing import List, Dict
import requests
import config
import database

# SMS Templates - Short, punchy, action-oriented
SMS_TEMPLATES = {
    'initial': """Hey {first_name}! Colin from CallAlly here.

Quick Q: Who answers your phone when you're on a job?

Most {vertical} companies lose 8-12 calls/day to voicemail. We fix that with AI that sounds human.

7-day free trial: callallynow.com/signup""",

    'followup_1': """Hey {first_name}, following up on CallAlly.

One captured call = $300-800. Missing 5/day = $50K+/year lost.

AI answers 24/7. Takes 10 min to set up.

Try free: callallynow.com/signup""",

    'followup_2': """{first_name} - last text from me.

Your competitors are answering calls at 10pm. Are you?

CallAlly: AI answers 24/7, books jobs, texts you details. $99/mo after free trial.

callallynow.com/signup""",

    'after_call': """Hey {first_name}! Great chatting. Here's that link:

callallynow.com/signup

7-day free trial. Takes 10 min. Text me if you have questions!

- Colin""",

    'hot_lead': """{first_name}! Saw you checked out CallAlly.

Want me to walk you through setup? Takes 10 min and you'll be live today.

Reply YES and I'll call you in 5 min."""
}

class SMSSender:
    """Automated SMS outreach using Twilio."""

    def __init__(self):
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.from_phone = config.TWILIO_PHONE
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"

    def send_sms(self, to_phone: str, message: str, lead_id: int = None) -> Dict:
        """Send a single SMS via Twilio."""
        if not self.account_sid or not self.auth_token:
            return {'success': False, 'error': 'Twilio not configured'}

        if not to_phone:
            return {'success': False, 'error': 'No phone number'}

        # Ensure phone format
        if not to_phone.startswith('+'):
            to_phone = f"+1{to_phone.replace('-', '').replace(' ', '')}"

        try:
            response = requests.post(
                f"{self.base_url}/Messages.json",
                auth=(self.account_sid, self.auth_token),
                data={
                    'From': self.from_phone,
                    'To': to_phone,
                    'Body': message
                }
            )

            if response.status_code in [200, 201]:
                result = response.json()
                if lead_id:
                    database.log_outreach(lead_id, 'sms', content=message, status='sent')
                return {'success': True, 'sid': result.get('sid')}
            else:
                error = response.json().get('message', 'Unknown error')
                if lead_id:
                    database.log_outreach(lead_id, 'sms', content=message, status='failed', error=error)
                return {'success': False, 'error': error}

        except Exception as e:
            if lead_id:
                database.log_outreach(lead_id, 'sms', content=message, status='error', error=str(e))
            return {'success': False, 'error': str(e)}

    def personalize_message(self, template_key: str, lead: Dict) -> str:
        """Personalize SMS template for lead."""
        template = SMS_TEMPLATES.get(template_key, SMS_TEMPLATES['initial'])

        first_name = 'there'
        if lead.get('owner_name'):
            first_name = lead['owner_name'].split()[0]

        return template.format(
            first_name=first_name,
            business_name=lead.get('business_name', 'your business'),
            vertical=lead.get('vertical', 'service'),
            city=lead.get('city', 'your city')
        )

    def send_sequence_sms(self, lead: Dict) -> Dict:
        """Send appropriate SMS based on where lead is in sequence."""
        sms_sent = lead.get('sms_sent', 0)

        if sms_sent == 0:
            template_key = 'initial'
        elif sms_sent == 1:
            template_key = 'followup_1'
        else:
            template_key = 'followup_2'

        message = self.personalize_message(template_key, lead)
        return self.send_sms(lead['phone'], message, lead['id'])

    def send_batch(self, leads: List[Dict], delay_seconds: float = 3.0) -> Dict:
        """Send SMS to a batch of leads."""
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }

        for lead in leads:
            if not lead.get('phone'):
                continue

            result = self.send_sequence_sms(lead)

            if result.get('success'):
                results['sent'] += 1
                print(f"✓ SMS sent to {lead['phone']} ({lead['business_name']})")
            else:
                results['failed'] += 1
                results['errors'].append({
                    'phone': lead['phone'],
                    'error': result.get('error')
                })
                print(f"✗ Failed: {lead['phone']} - {result.get('error')}")

            time.sleep(delay_seconds)

        return results

def run_sms_campaign(limit: int = None):
    """Run daily SMS campaign."""
    limit = limit or config.DAILY_SMS_LIMIT
    sender = SMSSender()

    print(f"\n{'='*50}")
    print(f"CallAlly SMS Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Get leads for SMS
    leads = database.get_leads_for_outreach(limit, 'sms')
    print(f"Found {len(leads)} leads for SMS outreach\n")

    if not leads:
        print("No leads ready for SMS.")
        return

    # Send SMS
    results = sender.send_batch(leads)

    print(f"\n{'='*50}")
    print(f"Results: {results['sent']} sent, {results['failed']} failed")
    print(f"{'='*50}\n")

    return results

# Quick SMS to specific number
def quick_sms(phone: str, name: str, template: str = 'initial'):
    """Send a quick SMS to a specific number."""
    sender = SMSSender()
    lead = {'owner_name': name, 'phone': phone, 'vertical': 'service'}
    message = sender.personalize_message(template, lead)
    return sender.send_sms(phone, message)

if __name__ == "__main__":
    run_sms_campaign(limit=10)
