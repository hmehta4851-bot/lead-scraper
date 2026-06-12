import sys
import time
from datetime import date

from config import PRODUCTS, SHEET_ID, SHEET_HEADERS, LEADS_PER_PRODUCT, TIER1_CITIES, TIER2_CITIES
from state import load_state, save_state, get_today_city, advance_city
from sheets import append_leads
from notifier import notify_tier1_exhausted, notify_tier2_exhausted, notify_daily_summary
from scrapers import indiamart, justdial, sulekha


def is_complete_lead(lead):
    required = ["company", "contact_person", "phone", "email", "designation"]
    return all(str(lead.get(f, "")).strip() for f in required)


def scrape_product(keyword_list, city, target=LEADS_PER_PRODUCT):
    all_raw = []

    for kw in keyword_list:
        print(f"  [IndiaMART] {kw} in {city}")
        results = indiamart.search(kw, city, max_results=30)
        all_raw.extend(results)
        time.sleep(1)

        if len([l for l in all_raw if is_complete_lead(l)]) >= target:
            break

        print(f"  [JustDial] {kw} in {city}")
        results = justdial.search(kw, city, max_results=30)
        all_raw.extend(results)
        time.sleep(1)

        if len([l for l in all_raw if is_complete_lead(l)]) >= target:
            break

        print(f"  [Sulekha] {kw} in {city}")
        results = sulekha.search(kw, city, max_results=20)
        all_raw.extend(results)
        time.sleep(1)

        if len([l for l in all_raw if is_complete_lead(l)]) >= target:
            break

    seen_phones = set()
    deduped = []
    for lead in all_raw:
        phone = str(lead.get("phone", "")).strip()
        if phone and phone not in seen_phones:
            seen_phones.add(phone)
            deduped.append(lead)

    complete = [l for l in deduped if is_complete_lead(l)]
    return complete[:target]


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
        print(f"  Complete leads found: {len(leads)}")

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
    return 0 if total_added > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
