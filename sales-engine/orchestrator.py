#!/usr/bin/env python3
"""
CallAlly Sales Engine - Master Orchestrator
=============================================
The brain that coordinates all sales activities.
Run this daily to execute the full sales machine.
"""

import sys
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict

import config
import database
from lead_scraper import run_scraper
from email_sender import run_email_campaign, EmailSender
from ai_caller import run_calling_campaign, AICaller
from sms_sender import run_sms_campaign, SMSSender

class SalesOrchestrator:
    """Master coordinator for all sales activities."""

    def __init__(self):
        self.email_sender = EmailSender()
        self.ai_caller = AICaller()
        self.sms_sender = SMSSender()
        database.init_database()

    def morning_routine(self):
        """Morning routine: scrape leads, send emails."""
        print("\n" + "="*60)
        print("CALLALLY SALES ENGINE - MORNING ROUTINE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

        # 1. Scrape new leads
        print("STEP 1: Scraping new leads...")
        print("-"*40)
        new_leads = run_scraper(
            verticals=['hvac', 'plumber', 'electrician'],
            cities=config.TARGET_CITIES[:10],
            limit_per_search=10
        )
        print(f"Added {new_leads} new leads\n")

        # 2. Send cold emails
        print("STEP 2: Sending cold emails...")
        print("-"*40)
        email_results = run_email_campaign(limit=config.DAILY_EMAIL_LIMIT)
        print(f"Emails: {email_results}\n")

        # 3. Show pipeline stats
        print("STEP 3: Pipeline Stats")
        print("-"*40)
        self.show_stats()

    def afternoon_routine(self):
        """Afternoon routine: AI calls to warm leads."""
        print("\n" + "="*60)
        print("CALLALLY SALES ENGINE - AFTERNOON CALLING")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

        # AI calls to leads who opened emails or visited site
        hot_leads = database.get_hot_leads(limit=config.DAILY_CALL_LIMIT)
        print(f"Found {len(hot_leads)} hot leads for calling\n")

        if hot_leads:
            call_results = run_calling_campaign(limit=len(hot_leads))
            print(f"Calls: {call_results}\n")

    def evening_routine(self):
        """Evening routine: SMS follow-ups."""
        print("\n" + "="*60)
        print("CALLALLY SALES ENGINE - EVENING SMS")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

        sms_results = run_sms_campaign(limit=config.DAILY_SMS_LIMIT)
        print(f"SMS: {sms_results}\n")

    def full_blitz(self):
        """FULL BLITZ MODE: All channels, maximum velocity."""
        print("\n" + "="*60)
        print("🔥 CALLALLY SALES ENGINE - FULL BLITZ MODE 🔥")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

        # Scrape aggressively
        print("BLITZ: Scraping ALL verticals, ALL cities...")
        run_scraper(
            verticals=list(config.VERTICALS.keys()),
            cities=config.TARGET_CITIES,
            limit_per_search=20
        )

        # Email everyone ready
        print("\nBLITZ: Emailing all leads...")
        run_email_campaign(limit=200)

        # SMS everyone ready
        print("\nBLITZ: SMS to all leads...")
        run_sms_campaign(limit=100)

        # Call hot leads
        print("\nBLITZ: Calling hot leads...")
        run_calling_campaign(limit=20)

        print("\n" + "="*60)
        print("BLITZ COMPLETE")
        self.show_stats()
        print("="*60 + "\n")

    def show_stats(self):
        """Display pipeline statistics."""
        stats = database.get_pipeline_stats()

        print(f"""
┌─────────────────────────────────────┐
│       CALLALLY PIPELINE STATS       │
├─────────────────────────────────────┤
│ Total Leads:     {stats['total_leads']:>6}              │
│ Conversion Rate: {stats['conversion_rate']:>5.1f}%             │
├─────────────────────────────────────┤
│ BY STATUS:                          │""")

        for status, count in stats.get('by_status', {}).items():
            print(f"│   {status:<15} {count:>6}            │")

        print("""├─────────────────────────────────────┤
│ TODAY'S OUTREACH:                   │""")

        for otype, count in stats.get('today_outreach', {}).items():
            print(f"│   {otype:<15} {count:>6}            │")

        print("""└─────────────────────────────────────┘
        """)

    def manual_outreach(self, email: str = None, phone: str = None,
                        business: str = None, name: str = None):
        """Manual outreach to a specific prospect."""
        if email:
            print(f"Sending email to {email}...")
            from email_sender import send_personal_email
            result = send_personal_email(email, name or 'there', business or 'your business')
            print(f"Result: {result}")

        if phone:
            print(f"Sending SMS to {phone}...")
            from sms_sender import quick_sms
            result = quick_sms(phone, name or 'there')
            print(f"Result: {result}")

    def hunt_first_customer(self):
        """AGGRESSIVE MODE: Hunt down the first customer ruthlessly."""
        print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🎯 HUNTING MODE: FIRST CUSTOMER ACQUISITION 🎯         ║
║                                                           ║
║   We will not stop until we get a customer.               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)

        # Phase 1: Load the pipeline
        print("\n[PHASE 1] Loading the pipeline...")
        print("="*50)

        # Focus on high-intent verticals first
        priority_verticals = ['hvac', 'plumber', 'electrician']
        priority_cities = [
            ('Phoenix', 'AZ'),  # Hot climate = HVAC pain
            ('Houston', 'TX'),  # Hot + humid = HVAC pain
            ('Miami', 'FL'),    # Hot = HVAC pain
            ('Dallas', 'TX'),
            ('Los Angeles', 'CA'),
        ]

        leads_added = run_scraper(
            verticals=priority_verticals,
            cities=priority_cities,
            limit_per_search=30
        )
        print(f"Pipeline loaded with {leads_added} fresh leads\n")

        # Phase 2: Multi-channel blitz
        print("\n[PHASE 2] Multi-channel outreach blitz...")
        print("="*50)

        # Email first (widest reach)
        print("\n📧 Sending emails...")
        email_results = run_email_campaign(limit=100)

        # SMS for quick touchpoint
        print("\n📱 Sending SMS...")
        sms_results = run_sms_campaign(limit=50)

        # Calls to hottest leads
        print("\n📞 Calling hottest leads...")
        call_results = run_calling_campaign(limit=10)

        # Phase 3: Status report
        print("\n[PHASE 3] Hunt Status Report")
        print("="*50)
        self.show_stats()

        print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   NEXT STEPS:                                             ║
║   1. Monitor for email opens/replies                      ║
║   2. Check call recordings for interested leads           ║
║   3. Follow up on SMS responses                           ║
║   4. Run this again in 24 hours                           ║
║                                                           ║
║   🎯 THE FIRST CUSTOMER IS OUT THERE. WE WILL FIND THEM. ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)

def main():
    parser = argparse.ArgumentParser(description='CallAlly Sales Engine')
    parser.add_argument('command', nargs='?', default='stats',
                       choices=['morning', 'afternoon', 'evening', 'blitz', 'hunt', 'stats', 'scrape'])
    parser.add_argument('--email', help='Email for manual outreach')
    parser.add_argument('--phone', help='Phone for manual outreach')
    parser.add_argument('--name', help='Name for manual outreach')
    parser.add_argument('--business', help='Business name for manual outreach')

    args = parser.parse_args()

    orchestrator = SalesOrchestrator()

    if args.email or args.phone:
        orchestrator.manual_outreach(
            email=args.email,
            phone=args.phone,
            name=args.name,
            business=args.business
        )
    elif args.command == 'morning':
        orchestrator.morning_routine()
    elif args.command == 'afternoon':
        orchestrator.afternoon_routine()
    elif args.command == 'evening':
        orchestrator.evening_routine()
    elif args.command == 'blitz':
        orchestrator.full_blitz()
    elif args.command == 'hunt':
        orchestrator.hunt_first_customer()
    elif args.command == 'scrape':
        run_scraper()
    else:
        orchestrator.show_stats()

if __name__ == "__main__":
    main()
