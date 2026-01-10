# CallAlly Sales Engine

**An AI-powered sales machine that hunts customers ruthlessly.**

This is a complete outbound sales automation system that:
- Scrapes leads from Google Maps & Yelp
- Sends personalized cold emails via Resend
- Makes AI cold calls via Vapi
- Sends SMS follow-ups via Twilio
- Tracks everything in SQLite
- Runs automated multi-touch sequences

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 3. Initialize database
python database.py

# 4. Load email sequences
python -c "from database import init_database; init_database()"

# 5. HUNT MODE - Get that first customer
python orchestrator.py hunt
```

## Commands

```bash
# Full blitz - all channels, maximum velocity
python orchestrator.py blitz

# Daily routines
python orchestrator.py morning   # Scrape leads + send emails
python orchestrator.py afternoon # AI calls to warm leads
python orchestrator.py evening   # SMS follow-ups

# View pipeline stats
python orchestrator.py stats

# Just scrape leads
python orchestrator.py scrape

# Manual outreach to specific prospect
python orchestrator.py --email john@acmeplumbing.com --name John --business "Acme Plumbing"
```

## API Keys Needed

| Service | Purpose | Get it at |
|---------|---------|-----------|
| **Resend** | Email outreach | [resend.com](https://resend.com) |
| **Twilio** | SMS outreach | [twilio.com](https://twilio.com) |
| **Vapi** | AI cold calls | [vapi.ai](https://vapi.ai) |
| **Google Maps** | Lead scraping | [console.cloud.google.com](https://console.cloud.google.com) |
| **Yelp** | Lead scraping | [yelp.com/developers](https://www.yelp.com/developers) |

## Architecture

```
sales-engine/
├── orchestrator.py      # Main controller - run this
├── config.py           # Settings and API keys
├── database.py         # SQLite lead tracking
├── lead_scraper.py     # Google Maps + Yelp scraping
├── email_sender.py     # Resend email automation
├── ai_caller.py        # Vapi AI cold calling
├── sms_sender.py       # Twilio SMS automation
├── linkedin_outreach.py # LinkedIn messaging
└── sales.db            # SQLite database (auto-created)
```

## Email Sequences

Pre-loaded sequences for:
- HVAC companies (4-step)
- Plumbers (2-step)
- Electricians (1-step)
- Dental practices (1-step)
- General/all verticals (1-step)

Each sequence is personalized with:
- `{{business_name}}` - Company name
- `{{first_name}}` - Owner's first name
- `{{city}}` / `{{state}}` - Location
- `{{vertical}}` - Industry

## Target Verticals

- HVAC / Air Conditioning
- Plumbing
- Electrical
- Dental
- Roofing
- Garage Door
- Locksmith
- Pest Control
- Landscaping
- Cleaning Services

## Daily Limits (Configurable)

- Emails: 100/day
- Calls: 50/day
- SMS: 50/day

## Lead Scoring

Leads are scored based on:
- Email opens (+5)
- Link clicks (+10)
- Replies (+25)
- Call answered (+15)
- Website visits (+20)

Hot leads are prioritized for calls.

## Cron Setup (Automated Daily)

```bash
# Add to crontab -e

# Morning routine at 9am
0 9 * * * cd /path/to/sales-engine && python orchestrator.py morning

# Afternoon calls at 2pm
0 14 * * * cd /path/to/sales-engine && python orchestrator.py afternoon

# Evening SMS at 6pm
0 18 * * * cd /path/to/sales-engine && python orchestrator.py evening
```

## The Philosophy

**Hunt ruthlessly. Be human.**

- Every email sounds like a real person wrote it
- Every call sounds like a real conversation
- Every touchpoint provides value
- Follow up until they buy or tell you to stop

The first customer is out there. This machine will find them.

---

Built for CallAlly. Stop losing customers to voicemail.
