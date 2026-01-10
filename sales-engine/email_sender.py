"""
CallAlly Sales Engine - Email Outreach System
===============================================
Automated email outreach using Resend API.
"""

import re
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
import config
import database

class EmailSender:
    """Automated email outreach system."""

    def __init__(self):
        self.api_key = config.RESEND_API_KEY
        self.from_email = config.FROM_EMAIL
        self.base_url = "https://api.resend.com"

    def personalize_email(self, template: str, lead: Dict) -> str:
        """Replace placeholders with lead data."""
        replacements = {
            '{{business_name}}': lead.get('business_name', 'your business'),
            '{{first_name}}': self.extract_first_name(lead.get('owner_name')),
            '{{city}}': lead.get('city', 'your city'),
            '{{state}}': lead.get('state', ''),
            '{{vertical}}': lead.get('vertical', 'service'),
            '{{phone}}': lead.get('phone', ''),
        }

        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value or '')

        return result

    def extract_first_name(self, full_name: Optional[str]) -> str:
        """Extract first name or return default."""
        if not full_name:
            return "there"
        parts = full_name.strip().split()
        return parts[0] if parts else "there"

    def send_email(self, to_email: str, subject: str, body: str,
                   lead_id: int = None) -> Dict:
        """Send a single email via Resend API."""
        if not self.api_key:
            return {'success': False, 'error': 'API key not configured'}

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Convert plain text to HTML
        html_body = self.text_to_html(body)

        payload = {
            'from': self.from_email,
            'to': [to_email],
            'subject': subject,
            'html': html_body,
            'text': body,
            'reply_to': config.REPLY_TO
        }

        try:
            response = requests.post(
                f"{self.base_url}/emails",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                result = {'success': True, 'id': response.json().get('id')}
                if lead_id:
                    database.log_outreach(lead_id, 'email', subject, body, 'sent')
                return result
            else:
                error = response.json().get('message', 'Unknown error')
                if lead_id:
                    database.log_outreach(lead_id, 'email', subject, body, 'failed', error)
                return {'success': False, 'error': error}

        except Exception as e:
            if lead_id:
                database.log_outreach(lead_id, 'email', subject, body, 'error', str(e))
            return {'success': False, 'error': str(e)}

    def text_to_html(self, text: str) -> str:
        """Convert plain text email to simple HTML."""
        # Escape HTML
        html = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Convert line breaks
        html = html.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br>')

        # Make URLs clickable
        url_pattern = r'(https?://[^\s<]+)'
        html = re.sub(url_pattern, r'<a href="\1" style="color: #f59e0b;">\1</a>', html)

        # Wrap in styled container
        return f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 15px; line-height: 1.6; color: #334155; max-width: 600px;">
            <p>{html}</p>
        </div>
        """

    def send_sequence_email(self, lead: Dict, step: int = 1) -> Dict:
        """Send the appropriate sequence email to a lead."""
        vertical = lead.get('vertical', 'general')

        # Get email template
        template = database.get_email_sequence(vertical, step)
        if not template:
            template = database.get_email_sequence('all', step)

        if not template:
            return {'success': False, 'error': f'No template for step {step}'}

        # Personalize
        subject = self.personalize_email(template['subject'], lead)
        body = self.personalize_email(template['body'], lead)

        # Send
        return self.send_email(lead['email'], subject, body, lead['id'])

    def send_batch(self, leads: List[Dict], step: int = 1,
                   delay_seconds: float = 2.0) -> Dict:
        """Send emails to a batch of leads."""
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }

        for lead in leads:
            if not lead.get('email'):
                continue

            # Determine which step to send
            emails_sent = lead.get('emails_sent', 0)
            next_step = emails_sent + 1

            result = self.send_sequence_email(lead, next_step)

            if result.get('success'):
                results['sent'] += 1
                print(f"✓ Sent to {lead['email']} (step {next_step})")
            else:
                results['failed'] += 1
                results['errors'].append({
                    'email': lead['email'],
                    'error': result.get('error')
                })
                print(f"✗ Failed: {lead['email']} - {result.get('error')}")

            time.sleep(delay_seconds)  # Rate limiting

        return results

def run_email_campaign(limit: int = None):
    """Run daily email campaign."""
    limit = limit or config.DAILY_EMAIL_LIMIT
    sender = EmailSender()

    print(f"\n{'='*50}")
    print(f"CallAlly Email Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Get leads for outreach
    leads = database.get_leads_for_outreach(limit, 'email')
    print(f"Found {len(leads)} leads for email outreach\n")

    if not leads:
        print("No leads ready for outreach.")
        return

    # Send emails
    results = sender.send_batch(leads)

    print(f"\n{'='*50}")
    print(f"Results: {results['sent']} sent, {results['failed']} failed")
    print(f"{'='*50}\n")

    return results

# Quick one-off email for hot leads
def send_personal_email(email: str, name: str, business: str):
    """Send a personalized one-off email."""
    sender = EmailSender()

    subject = f"Quick question about {business}"
    body = f"""Hey {name},

I saw {business} online and had a quick question.

How many calls are you missing when you're on a job? Most service businesses lose 8-12 calls a day to voicemail.

We built CallAlly to fix this - AI that answers your calls 24/7, books appointments, and texts you the details. Sounds human. Takes 10 min to set up.

Worth a quick look?

https://callallynow.com/signup

- Colin
CallAlly

P.S. 7-day free trial. One captured job pays for months of service."""

    return sender.send_email(email, subject, body)

if __name__ == "__main__":
    run_email_campaign(limit=10)  # Test with 10
