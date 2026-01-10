#!/usr/bin/env python3
"""
🎯 HUNT MODE
============
One command to rule them all.
Run this to start hunting for that first customer.

Usage:
    python hunt.py
"""

import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_setup():
    """Check if everything is set up correctly."""
    issues = []

    # Check for .env
    if not os.path.exists('.env'):
        issues.append("Missing .env file - copy from .env.example and add your API keys")

    # Check for required packages
    try:
        import requests
    except ImportError:
        issues.append("Missing 'requests' - run: pip install -r requirements.txt")

    if issues:
        print("\n⚠️  SETUP ISSUES FOUND:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nFix these issues and run again.\n")
        return False

    return True

def init_sequences():
    """Initialize database with email sequences."""
    import database
    database.init_database()

    # Check if sequences exist
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM email_sequences")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        print("Loading email sequences...")
        # Load the sequences
        conn = database.get_connection()
        cursor = conn.cursor()

        sequences = [
            # HVAC
            ('hvac_cold', 'hvac', 1, 0, 'Quick question about {{business_name}}',
             '''Hey {{first_name}},

I noticed {{business_name}} has solid reviews. Quick question - how many calls are you missing when your techs are on jobs?

Most HVAC companies lose 8-12 calls a day to voicemail. At $350/job, that's $50K+/year walking to competitors.

We built CallAlly to fix this. AI answers your calls 24/7, books appointments, texts you the details. Sounds human. 10 min setup.

Worth a quick look?

callallynow.com/signup

- Colin

P.S. 7-day free trial, cancel anytime.'''),

            ('hvac_cold', 'hvac', 2, 2, 'The math on missed calls',
             '''{{first_name}},

Quick calculation for {{business_name}}:

5 missed calls/day × $350 job × 30% close rate = $191,625/year lost.

Even if I'm half wrong, that's still $95K.

CallAlly answers every call in under a second. No voicemail. No lost leads. $99/month.

One emergency call pays for the whole year.

callallynow.com/signup

- Colin'''),

            ('hvac_cold', 'hvac', 3, 4, 'What happens at 10pm',
             '''{{first_name}},

AC dies at 10pm. July. 95 degrees.

They call 3 companies:
- Company 1: Voicemail
- Company 2: Voicemail
- Company 3 (you + CallAlly): "I'm so sorry. Let me get you scheduled for first thing. What's your address?"

Who gets the $800 call?

40% of service calls come after 5pm.

callallynow.com/signup

- Colin'''),

            # Plumber
            ('plumber_cold', 'plumber', 1, 0, 'Quick question for {{business_name}}',
             '''Hey {{first_name}},

When you're under a sink or snaking a drain, who answers your phone?

Most plumbers: "voicemail." Which means the customer calls the next guy.

CallAlly - AI answers 24/7, sounds human, books the job, texts you details. $99/month.

One emergency call = pays for the whole year.

callallynow.com/signup

- Colin'''),

            # Electrician
            ('electrician_cold', 'electrician', 1, 0, 'Missing calls = missing revenue',
             '''Hey {{first_name}},

Quick math for {{business_name}}:

5 missed calls/day × $400 job × 30% close = $219K/year lost.

You can't answer on a ladder or in a panel. I get it.

CallAlly can. AI answers 24/7, books jobs, texts you. Sounds human. 10 min setup.

$99/month. One job pays for the year.

callallynow.com/signup

- Colin'''),

            # General
            ('general_cold', 'all', 1, 0, 'You might be losing $50K/year to voicemail',
             '''Hey {{first_name}},

62% of calls to small businesses go unanswered. Those callers don't leave messages. They call your competitor.

CallAlly fixes this. AI answers 24/7, books appointments, texts you details. Sounds remarkably human.

$99/month. 10 min setup. 7-day free trial.

One captured job pays for months.

callallynow.com/signup

- Colin

P.S. 30-day money-back guarantee. If it doesn't pay for itself, get every penny back.'''),

            ('general_cold', 'all', 2, 3, 'Following up',
             '''{{first_name}},

Following up on CallAlly. Quick question:

What happens when someone calls {{business_name}} after hours or when you're on a job?

If the answer is "voicemail" - you're losing money. 85% of callers don't leave messages. They call the next business.

CallAlly answers every call. 24/7. Sounds human. Books appointments. Texts you immediately.

$99/month. 7-day free trial.

callallynow.com/signup

- Colin'''),
        ]

        for seq in sequences:
            cursor.execute("""
                INSERT INTO email_sequences (name, vertical, step, delay_days, subject, body)
                VALUES (?, ?, ?, ?, ?, ?)
            """, seq)

        conn.commit()
        conn.close()
        print(f"Loaded {len(sequences)} email sequences.")

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           🎯 CALLALLY SALES ENGINE - HUNT MODE 🎯         ║
║                                                           ║
║           Hunting for that first customer...              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Check setup
    if not check_setup():
        sys.exit(1)

    # Initialize
    print("Initializing database...")
    init_sequences()

    # Run the hunt
    print("\nStarting the hunt...\n")
    from orchestrator import SalesOrchestrator
    orchestrator = SalesOrchestrator()
    orchestrator.hunt_first_customer()

if __name__ == "__main__":
    main()
