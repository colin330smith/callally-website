"""
CallAlly Sales Engine - Database Manager
==========================================
SQLite database for lead tracking and pipeline management.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import config

def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Leads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            owner_name TEXT,
            email TEXT,
            phone TEXT,
            website TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            vertical TEXT,
            source TEXT,
            status TEXT DEFAULT 'new',
            last_contact TEXT,
            next_followup TEXT,
            emails_sent INTEGER DEFAULT 0,
            calls_made INTEGER DEFAULT 0,
            sms_sent INTEGER DEFAULT 0,
            linkedin_sent INTEGER DEFAULT 0,
            notes TEXT,
            score INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(email),
            UNIQUE(phone)
        )
    """)

    # Outreach log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outreach_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            subject TEXT,
            content TEXT,
            status TEXT,
            response TEXT,
            error TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)

    # Email sequences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            vertical TEXT,
            step INTEGER NOT NULL,
            delay_days INTEGER DEFAULT 0,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    # Call scripts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            vertical TEXT,
            script TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    # Pipeline stages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            stage TEXT NOT NULL,
            entered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            exited_at TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def add_lead(lead: Dict) -> Optional[int]:
    """Add a new lead to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO leads (
                business_name, owner_name, email, phone, website,
                address, city, state, vertical, source, status,
                next_followup
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
        """, (
            lead.get('business_name'),
            lead.get('owner_name'),
            lead.get('email'),
            lead.get('phone'),
            lead.get('website'),
            lead.get('address'),
            lead.get('city'),
            lead.get('state'),
            lead.get('vertical'),
            lead.get('source'),
            datetime.now().isoformat()
        ))
        conn.commit()
        lead_id = cursor.lastrowid

        # Add to pipeline
        cursor.execute("""
            INSERT INTO pipeline (lead_id, stage) VALUES (?, 'new')
        """, (lead_id,))
        conn.commit()

        return lead_id
    except sqlite3.IntegrityError:
        # Duplicate email or phone
        return None
    finally:
        conn.close()

def bulk_add_leads(leads: List[Dict]) -> int:
    """Add multiple leads, return count of successfully added."""
    added = 0
    for lead in leads:
        if add_lead(lead):
            added += 1
    return added

def get_leads_for_outreach(limit: int = 50, outreach_type: str = 'email') -> List[Dict]:
    """Get leads ready for outreach."""
    conn = get_connection()
    cursor = conn.cursor()

    if outreach_type == 'email':
        # Get leads with email, not contacted recently, under email limit
        cursor.execute("""
            SELECT * FROM leads
            WHERE email IS NOT NULL
            AND email != ''
            AND status NOT IN ('converted', 'unsubscribed', 'bounced', 'dead')
            AND (last_contact IS NULL OR last_contact < datetime('now', '-1 day'))
            AND emails_sent < 5
            ORDER BY
                CASE WHEN emails_sent = 0 THEN 0 ELSE 1 END,
                created_at ASC
            LIMIT ?
        """, (limit,))
    elif outreach_type == 'call':
        cursor.execute("""
            SELECT * FROM leads
            WHERE phone IS NOT NULL
            AND phone != ''
            AND status NOT IN ('converted', 'do_not_call', 'dead')
            AND (last_contact IS NULL OR last_contact < datetime('now', '-2 day'))
            AND calls_made < 3
            ORDER BY
                CASE WHEN calls_made = 0 THEN 0 ELSE 1 END,
                score DESC,
                created_at ASC
            LIMIT ?
        """, (limit,))
    elif outreach_type == 'sms':
        cursor.execute("""
            SELECT * FROM leads
            WHERE phone IS NOT NULL
            AND phone != ''
            AND status NOT IN ('converted', 'do_not_call', 'dead')
            AND sms_sent < 3
            ORDER BY
                CASE WHEN sms_sent = 0 THEN 0 ELSE 1 END,
                score DESC
            LIMIT ?
        """, (limit,))

    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return leads

def log_outreach(lead_id: int, outreach_type: str, subject: str = None,
                 content: str = None, status: str = 'sent', error: str = None):
    """Log an outreach attempt."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO outreach_log (lead_id, type, subject, content, status, error)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lead_id, outreach_type, subject, content, status, error))

    # Update lead counts
    if outreach_type == 'email':
        cursor.execute("UPDATE leads SET emails_sent = emails_sent + 1, last_contact = ?, updated_at = ? WHERE id = ?",
                      (datetime.now().isoformat(), datetime.now().isoformat(), lead_id))
    elif outreach_type == 'call':
        cursor.execute("UPDATE leads SET calls_made = calls_made + 1, last_contact = ?, updated_at = ? WHERE id = ?",
                      (datetime.now().isoformat(), datetime.now().isoformat(), lead_id))
    elif outreach_type == 'sms':
        cursor.execute("UPDATE leads SET sms_sent = sms_sent + 1, last_contact = ?, updated_at = ? WHERE id = ?",
                      (datetime.now().isoformat(), datetime.now().isoformat(), lead_id))

    conn.commit()
    conn.close()

def update_lead_status(lead_id: int, status: str, notes: str = None):
    """Update lead status."""
    conn = get_connection()
    cursor = conn.cursor()

    if notes:
        cursor.execute("""
            UPDATE leads SET status = ?, notes = ?, updated_at = ? WHERE id = ?
        """, (status, notes, datetime.now().isoformat(), lead_id))
    else:
        cursor.execute("""
            UPDATE leads SET status = ?, updated_at = ? WHERE id = ?
        """, (status, datetime.now().isoformat(), lead_id))

    conn.commit()
    conn.close()

def update_lead_score(lead_id: int, score_delta: int):
    """Increase/decrease lead score based on engagement."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE leads SET score = score + ?, updated_at = ? WHERE id = ?
    """, (score_delta, datetime.now().isoformat(), lead_id))
    conn.commit()
    conn.close()

def get_email_sequence(vertical: str, step: int) -> Optional[Dict]:
    """Get email template for vertical and step."""
    conn = get_connection()
    cursor = conn.cursor()

    # Try vertical-specific first
    cursor.execute("""
        SELECT * FROM email_sequences
        WHERE (vertical = ? OR vertical = 'all')
        AND step = ?
        AND active = 1
        ORDER BY CASE WHEN vertical = ? THEN 0 ELSE 1 END
        LIMIT 1
    """, (vertical, step, vertical))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

def get_pipeline_stats() -> Dict:
    """Get pipeline statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    stats = {}

    # Total leads
    cursor.execute("SELECT COUNT(*) FROM leads")
    stats['total_leads'] = cursor.fetchone()[0]

    # By status
    cursor.execute("""
        SELECT status, COUNT(*) as count FROM leads GROUP BY status
    """)
    stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}

    # By vertical
    cursor.execute("""
        SELECT vertical, COUNT(*) as count FROM leads GROUP BY vertical
    """)
    stats['by_vertical'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Today's outreach
    cursor.execute("""
        SELECT type, COUNT(*) as count FROM outreach_log
        WHERE date(sent_at) = date('now')
        GROUP BY type
    """)
    stats['today_outreach'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Conversion rate
    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'converted'")
    converted = cursor.fetchone()[0]
    stats['conversion_rate'] = (converted / stats['total_leads'] * 100) if stats['total_leads'] > 0 else 0

    conn.close()
    return stats

def get_hot_leads(limit: int = 20) -> List[Dict]:
    """Get highest-scoring leads."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM leads
        WHERE status NOT IN ('converted', 'dead', 'unsubscribed')
        ORDER BY score DESC, updated_at DESC
        LIMIT ?
    """, (limit,))

    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return leads

if __name__ == "__main__":
    init_database()
