import sys
import time
from datetime import date

from config import PRODUCTS, SHEET_ID, SHEET_HEADERS, LEADS_PER_PRODUCT, TIER1_CITIES, TIER2_CITIES
from state import load_state, get_today_city, advance_city
from sheets import append_leads
from notifier import notify_tier1_exhausted, notify_tier2_exhausted, notify_daily_summary
from scrapers import sulekha, googlemaps
from scrapers import browser as scraper_browser


def is_actionable_lead(lead):
    """A company with a callable phone number is usable by the sales team."""
    required = ["company", "phone"]
    return all(str(lead.get(f, "")).strip() for f in required)


def scrape_product(keyword_list, city, target=LEADS_PER_PRODUCT):
    all_raw = []

    for kw in keyword_list:
        # Google Maps — primary source (works for all product types)
        print(f"  [Google Maps] {kw} in {city}")
        results = googlemaps.search(kw, city, max_results=20)
        all_raw.extend(results)
        time.sleep(1)

        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # Sulekha — secondary source (strong for service contractors)
        print(f"  [Sulekha] {kw} in {city}")
        results = sulekha.search(kw, city, max_results=15)
        all_raw.extend(results)
        time.sleep(1)

        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

    seen_phones = set()
    deduped = []
    for lead in all_raw:
        phone = str(lead.get("phone", "")).strip()
        if phone and phone not in seen_phones:
            seen_phones.add(phone)
            deduped.append(lead)

    actionable = [lead for lead in deduped if is_actionable_lead(lead)]
    return actionable[:target]


def format_lead_row(lead, product_name, city):
    return {
        "Date": str(date.today()),
        "City": city,
        "Product": product_name,
        "Company Name": lead.get("company", ""),
        "Contact Person": lead.get("contact_person", ""),
        "Phone": lead.get("phone", ""),
        "Email": lead.get("email", ""),
        "Designation": lead.get("designation", ""),
        "Source": lead.get("source", ""),
        "Website": lead.get("website", ""),
    }


def main():
    try:
        state = load_state()
        city = get_today_city(state, TIER1_CITIES, TIER2_CITIES)

        print(f"\n=== Lead Scraper | {date.today()} | City: {city} | Tier {state['tier']} ===\n")

        was_tier1_exhausted = state.get("exhausted_tier1", False)
        was_tier2_exhausted = state.get("exhausted_tier2", False)

        per_product_counts = {}
        total_added = 0

        for product_name, product_cfg in PRODUCTS.items():
            print(f"\n[{product_name}] Scraping {city}...")
            leads = scrape_product(product_cfg["keywords"], city, LEADS_PER_PRODUCT)
            print(f"  Actionable leads found: {len(leads)}")

            if not leads:
                per_product_counts[product_name] = 0
                continue

            rows = [format_lead_row(l, product_name, city) for l in leads]
            added = append_leads(SHEET_ID, product_cfg["tab"], SHEET_HEADERS, rows)
            per_product_counts[product_name] = added
            total_added += added
            print(f"  Added to sheet: {added}")

            time.sleep(2)

        advance_city(state, TIER1_CITIES, TIER2_CITIES)
        new_state = load_state()

        if not was_tier1_exhausted and new_state.get("exhausted_tier1"):
            print("\n[NOTIFY] Tier 1 exhausted — sending email")
            notify_tier1_exhausted()

        if not was_tier2_exhausted and new_state.get("exhausted_tier2"):
            print("\n[NOTIFY] Tier 2 exhausted — sending email")
            notify_tier2_exhausted()

        notify_daily_summary(city, total_added, per_product_counts)

        print(f"\n=== Done. Total leads added today: {total_added} ===\n")
        # A completed run with no new leads is still successful; duplicates or
        # temporarily empty search results should not fail the scheduled job.
        return 0
    finally:
        scraper_browser.close()


if __name__ == "__main__":
    sys.exit(main())
