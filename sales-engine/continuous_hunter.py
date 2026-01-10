#!/usr/bin/env python3
"""
CallAlly Continuous Sales Hunter
==================================
Runs 24/7 in the background, hunting for customers.

- Sends follow-up emails every 2 days
- Adds new leads continuously
- Tracks all activity
"""

import time
import schedule
from datetime import datetime
import database
from email_sender import run_email_campaign

def log(message):
    """Log with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    with open('hunter.log', 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def morning_emails():
    """Send morning email batch."""
    log("Starting morning email campaign...")
    try:
        results = run_email_campaign(limit=50)
        log(f"Emails sent: {results.get('sent', 0)}, failed: {results.get('failed', 0)}")
    except Exception as e:
        log(f"Error in morning emails: {e}")

def afternoon_followups():
    """Send afternoon follow-ups."""
    log("Starting afternoon follow-ups...")
    try:
        results = run_email_campaign(limit=30)
        log(f"Follow-ups sent: {results.get('sent', 0)}")
    except Exception as e:
        log(f"Error in afternoon follow-ups: {e}")

def show_stats():
    """Display current pipeline stats."""
    try:
        stats = database.get_pipeline_stats()
        log(f"Pipeline: {stats.get('total_leads', 0)} leads, {stats.get('conversion_rate', 0):.1f}% conversion")
    except Exception as e:
        log(f"Error getting stats: {e}")

def run_continuous():
    """Run the continuous hunter."""
    log("="*60)
    log("CALLALLY CONTINUOUS HUNTER STARTED")
    log("="*60)

    # Initialize
    database.init_database()

    # Schedule tasks
    schedule.every().day.at("09:00").do(morning_emails)
    schedule.every().day.at("14:00").do(afternoon_followups)
    schedule.every().hour.do(show_stats)

    # Run immediately on start
    log("Running initial campaign...")
    morning_emails()
    show_stats()

    log("Scheduler started. Running every scheduled time.")
    log("Press Ctrl+C to stop.")

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_continuous()
