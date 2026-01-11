#!/usr/bin/env python3
"""
CallAlly AGGRESSIVE Sales Hunter
=================================
Runs 24/7 hunting for customers. Does not stop until we get signups.

- Sends emails every 2 hours during business hours
- Makes AI calls during optimal times
- Follow-up sequences on autopilot
- Tracks everything
"""

import time
import schedule
import sqlite3
from datetime import datetime, timedelta
import os
import sys

# Load env manually to avoid dotenv issues
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

import database
from email_sender import run_email_campaign

LOG_FILE = os.path.join(os.path.dirname(__file__), 'hunter.log')
DB_PATH = os.path.join(os.path.dirname(__file__), 'sales.db')

def log(message):
    """Log with timestamp to file and console."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def get_stats():
    """Get current pipeline stats."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM leads')
    total_leads = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM outreach_log WHERE status = "sent"')
    emails_sent = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT lead_id) FROM outreach_log WHERE type = "email" AND status = "sent"')
    leads_emailed = cursor.fetchone()[0]

    cursor.execute('SELECT stage, COUNT(*) FROM pipeline GROUP BY stage')
    pipeline = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {
        'total_leads': total_leads,
        'emails_sent': emails_sent,
        'leads_emailed': leads_emailed,
        'pipeline': pipeline
    }

def morning_blast():
    """Morning email campaign - 9 AM."""
    log("="*50)
    log("MORNING BLAST - Starting email campaign")
    try:
        results = run_email_campaign(limit=50)
        sent = results.get('sent', 0) if results else 0
        failed = results.get('failed', 0) if results else 0
        log(f"Morning blast complete: {sent} sent, {failed} failed")
    except Exception as e:
        log(f"ERROR in morning blast: {e}")

def midday_push():
    """Midday follow-ups - 12 PM."""
    log("="*50)
    log("MIDDAY PUSH - Follow-up emails")
    try:
        results = run_email_campaign(limit=30)
        sent = results.get('sent', 0) if results else 0
        log(f"Midday push complete: {sent} sent")
    except Exception as e:
        log(f"ERROR in midday push: {e}")

def afternoon_surge():
    """Afternoon surge - 3 PM."""
    log("="*50)
    log("AFTERNOON SURGE - More outreach")
    try:
        results = run_email_campaign(limit=40)
        sent = results.get('sent', 0) if results else 0
        log(f"Afternoon surge complete: {sent} sent")
    except Exception as e:
        log(f"ERROR in afternoon surge: {e}")

def evening_close():
    """Evening closer - 6 PM."""
    log("="*50)
    log("EVENING CLOSE - Final push")
    try:
        results = run_email_campaign(limit=20)
        sent = results.get('sent', 0) if results else 0
        log(f"Evening close complete: {sent} sent")
    except Exception as e:
        log(f"ERROR in evening close: {e}")

def hourly_check():
    """Hourly status check."""
    stats = get_stats()
    log(f"STATS: {stats['total_leads']} leads | {stats['emails_sent']} emails sent | {stats['leads_emailed']} unique contacts")

def run_continuous():
    """Run the continuous hunter - NEVER STOPS."""
    log("="*60)
    log("CALLALLY AGGRESSIVE SALES HUNTER - ACTIVATED")
    log("="*60)
    log("")
    log("Mission: Hunt down that first customer. Do not stop.")
    log("")

    # Initialize database
    database.init_database()

    # Show initial stats
    stats = get_stats()
    log(f"Starting with {stats['total_leads']} leads in database")
    log(f"Previously sent {stats['emails_sent']} emails")
    log("")

    # Schedule aggressive email campaigns
    schedule.every().day.at("09:00").do(morning_blast)    # 9 AM
    schedule.every().day.at("12:00").do(midday_push)      # 12 PM
    schedule.every().day.at("15:00").do(afternoon_surge)  # 3 PM
    schedule.every().day.at("18:00").do(evening_close)    # 6 PM
    schedule.every().hour.do(hourly_check)

    # Run immediately on start
    log("Running initial email blast...")
    morning_blast()
    hourly_check()

    log("")
    log("Scheduler running. Hunting 24/7.")
    log("Next campaigns scheduled for 9AM, 12PM, 3PM, 6PM daily.")
    log("")

    # Keep running forever
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            log("Hunter stopped by user")
            break
        except Exception as e:
            log(f"ERROR: {e}")
            time.sleep(300)  # Wait 5 min on error

if __name__ == "__main__":
    run_continuous()
