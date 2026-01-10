"""
CallAlly Sales Engine - Lead Scraper
======================================
Scrape leads from Google Maps, Yelp, and other sources.
"""

import re
import json
import time
import requests
from typing import List, Dict, Optional
from urllib.parse import quote
import config
import database

class LeadScraper:
    """Multi-source lead scraper for service businesses."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def scrape_google_maps(self, query: str, city: str, state: str, limit: int = 20) -> List[Dict]:
        """Scrape business listings from Google Maps API."""
        leads = []

        if not config.GOOGLE_MAPS_API_KEY:
            print("Google Maps API key not configured")
            return leads

        search_query = f"{query} in {city}, {state}"
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

        params = {
            'query': search_query,
            'key': config.GOOGLE_MAPS_API_KEY
        }

        try:
            response = self.session.get(url, params=params)
            data = response.json()

            for place in data.get('results', [])[:limit]:
                place_id = place.get('place_id')

                # Get detailed info
                detail_url = "https://maps.googleapis.com/maps/api/place/details/json"
                detail_params = {
                    'place_id': place_id,
                    'fields': 'name,formatted_phone_number,website,formatted_address',
                    'key': config.GOOGLE_MAPS_API_KEY
                }

                detail_response = self.session.get(detail_url, params=detail_params)
                details = detail_response.json().get('result', {})

                lead = {
                    'business_name': details.get('name', place.get('name')),
                    'phone': self.clean_phone(details.get('formatted_phone_number')),
                    'website': details.get('website'),
                    'address': details.get('formatted_address', place.get('formatted_address')),
                    'city': city,
                    'state': state,
                    'vertical': self.detect_vertical(query),
                    'source': 'google_maps'
                }

                # Try to extract email from website
                if lead['website']:
                    lead['email'] = self.extract_email_from_website(lead['website'])

                leads.append(lead)
                time.sleep(0.2)  # Rate limiting

        except Exception as e:
            print(f"Error scraping Google Maps: {e}")

        return leads

    def scrape_yelp(self, query: str, city: str, state: str, limit: int = 20) -> List[Dict]:
        """Scrape business listings from Yelp API."""
        leads = []

        if not config.YELP_API_KEY:
            print("Yelp API key not configured")
            return leads

        url = "https://api.yelp.com/v3/businesses/search"
        headers = {'Authorization': f'Bearer {config.YELP_API_KEY}'}

        params = {
            'term': query,
            'location': f"{city}, {state}",
            'limit': limit
        }

        try:
            response = self.session.get(url, headers=headers, params=params)
            data = response.json()

            for biz in data.get('businesses', []):
                lead = {
                    'business_name': biz.get('name'),
                    'phone': self.clean_phone(biz.get('phone')),
                    'address': ' '.join(biz.get('location', {}).get('display_address', [])),
                    'city': city,
                    'state': state,
                    'vertical': self.detect_vertical(query),
                    'source': 'yelp'
                }
                leads.append(lead)

        except Exception as e:
            print(f"Error scraping Yelp: {e}")

        return leads

    def scrape_from_search(self, query: str, city: str, state: str) -> List[Dict]:
        """Scrape leads using DuckDuckGo search (free, no API key)."""
        leads = []
        search_query = f"{query} {city} {state} phone email"

        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(search_query)}"
            response = self.session.get(url)

            # Extract business info from search results
            # This is a basic implementation - production would use proper parsing
            phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', response.text)
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', response.text)

            # Would need more sophisticated parsing for real use
            print(f"Found {len(phones)} phones and {len(emails)} emails from search")

        except Exception as e:
            print(f"Error in search scrape: {e}")

        return leads

    def extract_email_from_website(self, url: str) -> Optional[str]:
        """Try to extract email from a business website."""
        try:
            # Add timeout and limit response size
            response = self.session.get(url, timeout=5)
            content = response.text[:50000]  # First 50KB

            # Find emails
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)

            # Filter out common non-business emails
            exclude = ['example.com', 'domain.com', 'email.com', 'yourdomain', 'sentry']
            business_emails = [e for e in emails if not any(x in e.lower() for x in exclude)]

            # Prefer info@, contact@, office@, owner@
            priority = ['info@', 'contact@', 'office@', 'owner@', 'sales@']
            for prefix in priority:
                for email in business_emails:
                    if email.lower().startswith(prefix):
                        return email

            return business_emails[0] if business_emails else None

        except Exception:
            return None

    def clean_phone(self, phone: str) -> Optional[str]:
        """Clean and standardize phone number."""
        if not phone:
            return None
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        return None

    def detect_vertical(self, query: str) -> str:
        """Detect vertical from search query."""
        query_lower = query.lower()
        for vertical, terms in config.VERTICALS.items():
            for term in terms:
                if term in query_lower:
                    return vertical
        return 'general'

    def enrich_lead(self, lead: Dict) -> Dict:
        """Enrich lead with additional data."""
        # Try to find owner name from LinkedIn or website
        # Try to find email if missing
        # Validate phone number

        if lead.get('website') and not lead.get('email'):
            lead['email'] = self.extract_email_from_website(lead['website'])

        return lead

def run_scraper(verticals: List[str] = None, cities: List[tuple] = None, limit_per_search: int = 20):
    """Run the lead scraper for specified verticals and cities."""
    scraper = LeadScraper()

    verticals = verticals or list(config.VERTICALS.keys())[:3]  # Start with top 3
    cities = cities or config.TARGET_CITIES[:5]  # Start with 5 cities

    total_leads = 0

    for city, state in cities:
        for vertical in verticals:
            search_terms = config.VERTICALS.get(vertical, [vertical])

            for term in search_terms[:1]:  # Use first term only
                print(f"Scraping: {term} in {city}, {state}")

                # Try Google Maps first
                leads = scraper.scrape_google_maps(term, city, state, limit_per_search)

                # Fallback to Yelp
                if not leads:
                    leads = scraper.scrape_yelp(term, city, state, limit_per_search)

                # Enrich and save leads
                for lead in leads:
                    lead = scraper.enrich_lead(lead)
                    if lead.get('email') or lead.get('phone'):
                        result = database.add_lead(lead)
                        if result:
                            total_leads += 1

                print(f"  Added {len(leads)} leads")
                time.sleep(1)  # Be nice to APIs

    print(f"\nTotal new leads added: {total_leads}")
    return total_leads

if __name__ == "__main__":
    database.init_database()
    run_scraper()
