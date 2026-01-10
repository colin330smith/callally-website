"""
CallAlly Sales Engine - LinkedIn Outreach System
==================================================
Automated LinkedIn connection requests and messaging.

NOTE: LinkedIn automation requires careful execution to avoid account restrictions.
Use with browser automation (Playwright) or LinkedIn API partners.
"""

import time
import random
from datetime import datetime
from typing import List, Dict
import database

# LinkedIn Message Templates
LINKEDIN_TEMPLATES = {
    'connection_request': """Hey {first_name}! I noticed you run {business_name}.

Quick question - who answers your calls when you're busy with jobs? Would love to connect and share something that might help.

- Colin""",

    'first_message': """Thanks for connecting, {first_name}!

Quick question for you - how many calls does {business_name} miss when you're on a job?

Most {vertical} companies we talk to lose 8-12 calls/day to voicemail. That's $50K+/year walking to competitors.

We built CallAlly to fix this - AI that answers your calls 24/7, sounds human, books appointments.

Worth a quick look? callallynow.com""",

    'followup_1': """Hey {first_name}! Following up on my message about CallAlly.

Curious - when someone calls {business_name} after 5pm or on weekends, what happens?

That's when 40% of service calls come in. If you're not answering, they're calling the next result on Google.

CallAlly answers 24/7. Takes 10 min to set up. 7-day free trial.

Would that be helpful?""",

    'followup_2': """Last message from me, {first_name}.

If you're happy with how you handle calls, no worries at all.

But if you're losing jobs to voicemail, we should talk. One captured emergency call pays for months of CallAlly.

callallynow.com/signup - 7 day free trial

Either way, thanks for connecting!""",

    'response_interested': """That's great to hear, {first_name}!

Here's how to get started:
1. Go to callallynow.com/signup
2. Takes about 10 min to set up
3. Free for 7 days - no card needed to start

Once you're in, you can test it by calling your own number. Most people can't tell it's AI.

Any questions, just message me here. I'll help you get set up.

- Colin""",

    'response_objection_cost': """Totally fair question, {first_name}.

It's $99/month for most businesses. Here's how to think about it:

- Average job value: $300-500
- Calls missed per week: 10-20
- Close rate: 30%

That's $500-1500/week in lost revenue. $99/mo is one captured job every 3 months.

Plus, 7-day free trial and 30-day money-back guarantee. Zero risk to try it.

callallynow.com/signup"""
}

class LinkedInOutreach:
    """LinkedIn outreach system for B2B sales."""

    def __init__(self):
        self.daily_connection_limit = 20  # LinkedIn limits
        self.daily_message_limit = 50
        self.connection_delay = (60, 180)  # Random delay between actions (seconds)
        self.message_delay = (30, 90)

    def personalize_message(self, template_key: str, lead: Dict) -> str:
        """Personalize LinkedIn message template."""
        template = LINKEDIN_TEMPLATES.get(template_key, LINKEDIN_TEMPLATES['first_message'])

        first_name = 'there'
        if lead.get('owner_name'):
            first_name = lead['owner_name'].split()[0]

        return template.format(
            first_name=first_name,
            business_name=lead.get('business_name', 'your business'),
            vertical=lead.get('vertical', 'service'),
            city=lead.get('city', 'your area')
        )

    def search_prospects(self, vertical: str, city: str) -> List[Dict]:
        """
        Search LinkedIn for prospects.

        In production, this would use:
        - LinkedIn Sales Navigator API
        - Browser automation (Playwright)
        - Third-party tools (Phantombuster, etc.)
        """
        search_queries = {
            'hvac': 'HVAC owner OR "heating and cooling" owner OR "AC company" owner',
            'plumber': 'plumbing owner OR plumber owner OR "plumbing company" owner',
            'electrician': 'electrical contractor owner OR electrician owner',
            'dental': 'dental practice owner OR dentist owner',
            'roofing': 'roofing company owner OR roofer owner',
        }

        query = search_queries.get(vertical, f'{vertical} business owner')
        query += f' {city}'

        print(f"Search query: {query}")
        print("NOTE: Implement with LinkedIn Sales Navigator or Playwright")

        return []

    def send_connection_request(self, profile_url: str, note: str) -> Dict:
        """
        Send LinkedIn connection request.

        Requires browser automation in production.
        """
        print(f"Would send connection request to: {profile_url}")
        print(f"Note: {note[:100]}...")

        # In production:
        # 1. Use Playwright to navigate to profile
        # 2. Click Connect button
        # 3. Add note
        # 4. Send

        return {'success': True, 'status': 'simulated'}

    def send_message(self, profile_url: str, message: str, lead_id: int = None) -> Dict:
        """
        Send LinkedIn message to connection.

        Requires browser automation in production.
        """
        print(f"Would send message to: {profile_url}")
        print(f"Message: {message[:100]}...")

        if lead_id:
            database.log_outreach(lead_id, 'linkedin', content=message, status='sent')

        return {'success': True, 'status': 'simulated'}

    def run_connection_campaign(self, leads: List[Dict]) -> Dict:
        """Run LinkedIn connection request campaign."""
        results = {'sent': 0, 'failed': 0}

        for i, lead in enumerate(leads[:self.daily_connection_limit]):
            if not lead.get('linkedin_url'):
                continue

            note = self.personalize_message('connection_request', lead)
            result = self.send_connection_request(lead['linkedin_url'], note)

            if result.get('success'):
                results['sent'] += 1
            else:
                results['failed'] += 1

            # Random delay to avoid detection
            delay = random.randint(*self.connection_delay)
            print(f"Waiting {delay}s before next action...")
            time.sleep(delay)

        return results

    def run_message_campaign(self, leads: List[Dict]) -> Dict:
        """Run LinkedIn messaging campaign to existing connections."""
        results = {'sent': 0, 'failed': 0}

        for lead in leads[:self.daily_message_limit]:
            if not lead.get('linkedin_url'):
                continue

            linkedin_sent = lead.get('linkedin_sent', 0)

            if linkedin_sent == 0:
                template = 'first_message'
            elif linkedin_sent == 1:
                template = 'followup_1'
            else:
                template = 'followup_2'

            message = self.personalize_message(template, lead)
            result = self.send_message(lead['linkedin_url'], message, lead.get('id'))

            if result.get('success'):
                results['sent'] += 1
            else:
                results['failed'] += 1

            delay = random.randint(*self.message_delay)
            time.sleep(delay)

        return results

def generate_linkedin_search_urls():
    """Generate LinkedIn Sales Navigator search URLs for manual use."""
    print("\n" + "="*60)
    print("LinkedIn Sales Navigator Search URLs")
    print("="*60 + "\n")

    base_url = "https://www.linkedin.com/sales/search/people"

    searches = [
        ("HVAC Company Owners", "HVAC owner OR heating cooling owner"),
        ("Plumbing Company Owners", "plumbing owner OR plumber owner"),
        ("Electrical Contractors", "electrical contractor owner"),
        ("Dental Practice Owners", "dental practice owner OR dentist owner"),
        ("Roofing Company Owners", "roofing company owner"),
    ]

    cities = ['Phoenix', 'Houston', 'Dallas', 'Miami', 'Los Angeles']

    for name, query in searches:
        print(f"\n{name}:")
        for city in cities:
            full_query = f"{query} {city}"
            print(f"  {city}: Search for '{full_query}'")

    print("""
MANUAL PROCESS:
1. Open LinkedIn Sales Navigator
2. Use these search queries
3. Filter by: 2nd degree connections, Company size 1-50
4. Export to CSV or connect directly
5. Import leads into sales engine database
""")

if __name__ == "__main__":
    generate_linkedin_search_urls()
