#!/usr/bin/env python3
"""
CallAlly Sales Engine - Lead Importer
=======================================
Import leads from CSV, manual entry, or paste.

Usage:
    python import_leads.py                    # Interactive mode
    python import_leads.py leads.csv          # Import from CSV
    python import_leads.py --manual           # Add single lead manually
"""

import sys
import csv
import database

def import_from_csv(filepath: str) -> int:
    """Import leads from CSV file."""
    database.init_database()

    required_fields = ['business_name']
    optional_fields = ['owner_name', 'email', 'phone', 'website', 'address',
                       'city', 'state', 'vertical', 'source']

    added = 0
    skipped = 0

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip if no business name
            if not row.get('business_name'):
                skipped += 1
                continue

            lead = {field: row.get(field, '').strip() for field in required_fields + optional_fields}
            lead['source'] = lead.get('source') or 'csv_import'

            result = database.add_lead(lead)
            if result:
                added += 1
            else:
                skipped += 1

    print(f"\nImported {added} leads, skipped {skipped} (duplicates or invalid)")
    return added

def manual_entry():
    """Interactive manual lead entry."""
    database.init_database()

    print("\n" + "="*50)
    print("MANUAL LEAD ENTRY")
    print("="*50)
    print("Enter lead details (press Enter to skip optional fields)\n")

    lead = {}

    lead['business_name'] = input("Business Name (required): ").strip()
    if not lead['business_name']:
        print("Business name is required.")
        return

    lead['owner_name'] = input("Owner Name: ").strip() or None
    lead['email'] = input("Email: ").strip() or None
    lead['phone'] = input("Phone: ").strip() or None
    lead['website'] = input("Website: ").strip() or None
    lead['city'] = input("City: ").strip() or None
    lead['state'] = input("State: ").strip() or None

    verticals = ['hvac', 'plumber', 'electrician', 'dental', 'roofing',
                 'garage_door', 'locksmith', 'pest_control', 'landscaping', 'cleaning']
    print(f"\nVerticals: {', '.join(verticals)}")
    lead['vertical'] = input("Vertical: ").strip() or 'general'

    lead['source'] = 'manual'

    result = database.add_lead(lead)
    if result:
        print(f"\n✓ Lead added successfully (ID: {result})")
    else:
        print("\n✗ Failed to add lead (might be duplicate)")

def bulk_paste():
    """Paste multiple leads in bulk format."""
    database.init_database()

    print("\n" + "="*50)
    print("BULK PASTE MODE")
    print("="*50)
    print("""
Paste leads in this format (one per line):
business_name | email | phone | city | state | vertical

Example:
Acme Plumbing | john@acmeplumbing.com | 555-123-4567 | Phoenix | AZ | plumber
Bob's HVAC | bob@bobshvac.com | 555-987-6543 | Houston | TX | hvac

Enter 'DONE' on a new line when finished.
""")

    leads = []
    while True:
        line = input()
        if line.upper() == 'DONE':
            break
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 1:
                lead = {
                    'business_name': parts[0] if len(parts) > 0 else None,
                    'email': parts[1] if len(parts) > 1 else None,
                    'phone': parts[2] if len(parts) > 2 else None,
                    'city': parts[3] if len(parts) > 3 else None,
                    'state': parts[4] if len(parts) > 4 else None,
                    'vertical': parts[5] if len(parts) > 5 else 'general',
                    'source': 'bulk_paste'
                }
                leads.append(lead)

    if leads:
        added = database.bulk_add_leads(leads)
        print(f"\n✓ Added {added} of {len(leads)} leads")
    else:
        print("\nNo valid leads to add.")

def sample_leads():
    """Add sample leads for testing."""
    database.init_database()

    samples = [
        {
            'business_name': 'Phoenix Comfort HVAC',
            'owner_name': 'Mike Johnson',
            'email': 'mike@phoenixcomfort.com',
            'phone': '+16025551234',
            'city': 'Phoenix',
            'state': 'AZ',
            'vertical': 'hvac',
            'source': 'sample'
        },
        {
            'business_name': 'Houston Pro Plumbing',
            'owner_name': 'Sarah Williams',
            'email': 'sarah@houstonproplumbing.com',
            'phone': '+17135559876',
            'city': 'Houston',
            'state': 'TX',
            'vertical': 'plumber',
            'source': 'sample'
        },
        {
            'business_name': 'DFW Electric Masters',
            'owner_name': 'James Chen',
            'email': 'james@dfwelectric.com',
            'phone': '+12145554321',
            'city': 'Dallas',
            'state': 'TX',
            'vertical': 'electrician',
            'source': 'sample'
        },
        {
            'business_name': 'Miami Smile Dental',
            'owner_name': 'Dr. Lisa Garcia',
            'email': 'dr.garcia@miamismile.com',
            'phone': '+13055556789',
            'city': 'Miami',
            'state': 'FL',
            'vertical': 'dental',
            'source': 'sample'
        },
        {
            'business_name': 'LA Cool Air',
            'owner_name': 'Robert Kim',
            'email': 'robert@lacoolair.com',
            'phone': '+13235558765',
            'city': 'Los Angeles',
            'state': 'CA',
            'vertical': 'hvac',
            'source': 'sample'
        },
    ]

    added = database.bulk_add_leads(samples)
    print(f"\n✓ Added {added} sample leads for testing")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--manual':
            manual_entry()
        elif sys.argv[1] == '--bulk':
            bulk_paste()
        elif sys.argv[1] == '--sample':
            sample_leads()
        elif sys.argv[1].endswith('.csv'):
            import_from_csv(sys.argv[1])
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("\nUsage:")
            print("  python import_leads.py leads.csv    # Import from CSV")
            print("  python import_leads.py --manual     # Add single lead")
            print("  python import_leads.py --bulk       # Paste multiple leads")
            print("  python import_leads.py --sample     # Add sample leads")
    else:
        print("""
CallAlly Lead Importer
======================

Choose an option:
1. Import from CSV file
2. Add single lead manually
3. Bulk paste leads
4. Add sample leads (for testing)
        """)

        choice = input("Enter choice (1-4): ").strip()

        if choice == '1':
            filepath = input("Enter CSV filepath: ").strip()
            if filepath:
                import_from_csv(filepath)
        elif choice == '2':
            manual_entry()
        elif choice == '3':
            bulk_paste()
        elif choice == '4':
            sample_leads()
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
