import re
import sys
import time
from datetime import date

from config import PRODUCTS, SHEET_ID, SHEET_HEADERS, LEADS_PER_PRODUCT, TIER1_CITIES, TIER2_CITIES
from state import load_state, get_today_city, advance_city
from sheets import append_leads
from notifier import (
    notify_tier1_exhausted, notify_tier2_exhausted,
    notify_daily_summary, notify_scraper_started, notify_progress_update,
)
from scrapers import sulekha, googlemaps, indiamart, exportersindia
from scrapers import tradeindia, duckduckgo, bing, yellowpages, justdial
from scrapers import browser as scraper_browser
from enricher import enrich_website, resolve_contact_names


def is_actionable_lead(lead):
    """A company with a callable phone number is usable by the sales team."""
    required = ["company", "phone"]
    return all(str(lead.get(f, "")).strip() for f in required)


def _lead_score(lead) -> int:
    """Higher score = more complete data = better lead."""
    score = 0
    if lead.get("phone"): score += 3
    if lead.get("email"): score += 2
    if lead.get("contact_person"): score += 2
    if lead.get("website"): score += 1
    if lead.get("designation"): score += 1
    return score


def _norm_phone(p: str) -> str:
    digits = re.sub(r"\D", "", str(p))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else digits


_COMPANY_NOISE_RE = re.compile(
    r"\b(pvt\.?\s*ltd\.?|private\s+limited|limited|llp|inc\.?|india|co\.)\b",
    re.I,
)


def _norm_company(name: str) -> str:
    n = _COMPANY_NOISE_RE.sub("", name.lower()).strip()
    return re.sub(r"\s+", " ", n).strip()[:40]


def scrape_product(keyword_list, city, target=LEADS_PER_PRODUCT):
    all_raw = []

    for kw in keyword_list:
        # 1. Google Maps — primary (local businesses, all types)
        print(f"  [Google Maps] {kw} in {city}")
        results = googlemaps.search(kw, city, max_results=40)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 2. Sulekha — strong for service contractors
        print(f"  [Sulekha] {kw} in {city}")
        results = sulekha.search(kw, city, max_results=15)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 3. ExportersIndia — B2B suppliers and dealers
        print(f"  [ExportersIndia] {kw} in {city}")
        results = exportersindia.search(kw, city, max_results=20)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 4. IndiaMART — unmasked phones only
        print(f"  [IndiaMART] {kw} in {city}")
        results = indiamart.search(kw, city, max_results=25)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 5. TradeIndia — additional B2B directory
        print(f"  [TradeIndia] {kw} in {city}")
        results = tradeindia.search(kw, city, max_results=20)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 6. DuckDuckGo — web-wide organic search (finds businesses not on directories)
        print(f"  [DuckDuckGo] {kw} in {city}")
        results = duckduckgo.search(kw, city, max_results=15)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 7. Bing — different crawl index than DuckDuckGo
        print(f"  [Bing] {kw} in {city}")
        results = bing.search(kw, city, max_results=15)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 8. YellowPages India — SMB directory
        print(f"  [YellowPages] {kw} in {city}")
        results = yellowpages.search(kw, city, max_results=15)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

        # 9. JustDial — India's largest local directory (graceful fallback if blocked)
        print(f"  [JustDial] {kw} in {city}")
        results = justdial.search(kw, city, max_results=20)
        all_raw.extend(results)
        time.sleep(1)
        if len([l for l in all_raw if is_actionable_lead(l)]) >= target:
            break

    # Dedup: normalize phones + company names to catch duplicates across sources
    seen_phones: set = set()
    seen_keys: set = set()
    deduped = []
    for lead in all_raw:
        raw_phone = str(lead.get("phone", "")).strip()
        phone_norm = _norm_phone(raw_phone) if raw_phone else ""
        # Overwrite with normalized form so downstream is consistent
        if phone_norm:
            lead["phone"] = phone_norm
        company_key = _norm_company(str(lead.get("company", "")))
        if phone_norm:
            if phone_norm not in seen_phones:
                seen_phones.add(phone_norm)
                deduped.append(lead)
        elif lead.get("website") and company_key and company_key not in seen_keys:
            seen_keys.add(company_key)
            deduped.append(lead)

    # Enrich website-only leads — visit company site to resolve phone number
    no_phone = [l for l in deduped if not l.get("phone") and l.get("website")]
    if no_phone:
        print(f"  [Enricher] Resolving phones for {min(len(no_phone), 15)} website-only leads...")
        for lead in no_phone[:15]:
            try:
                enriched = enrich_website(lead["website"], max_pages=2)
                p = enriched.get("phone", "")
                if p and p not in seen_phones:
                    lead["phone"] = p
                    seen_phones.add(p)
                if enriched.get("email") and not lead.get("email"):
                    lead["email"] = enriched["email"]
                if enriched.get("contact_person") and not lead.get("contact_person"):
                    lead["contact_person"] = enriched["contact_person"]
                    lead["designation"] = enriched.get("designation", "")
            except Exception:
                pass

    actionable = [l for l in deduped if is_actionable_lead(l)]
    # Sort by data completeness — best leads first, then take top N
    actionable.sort(key=_lead_score, reverse=True)
    top = actionable[:target]

    # Enrich top leads — fill email + contact person from company website (free)
    needs_enrich = [
        l for l in top
        if l.get("website") and (not l.get("email") or not l.get("contact_person"))
    ]
    if needs_enrich:
        print(f"  [Enricher] Enriching {min(len(needs_enrich), 10)} leads for email & contact...")
        for lead in needs_enrich[:10]:
            try:
                enriched = enrich_website(lead["website"], max_pages=2)
                if not lead.get("email") and enriched.get("email"):
                    lead["email"] = enriched["email"]
                if not lead.get("contact_person") and enriched.get("contact_person"):
                    lead["contact_person"] = enriched["contact_person"]
                    lead["designation"] = enriched.get("designation", lead.get("designation", ""))
            except Exception:
                pass

    # Parallel web-search fallback for any leads still missing a contact name
    resolve_contact_names(top, city)

    return top


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
        total_products = len(PRODUCTS)

        try:
            notify_scraper_started(city, total_products)
        except Exception as e:
            print(f"[NOTIFY WARN] Start notification failed: {e}")

        run_start = time.time()
        last_progress_notify = run_start
        PROGRESS_INTERVAL = 10 * 60  # 10 minutes

        for idx, (product_name, product_cfg) in enumerate(PRODUCTS.items(), start=1):
            print(f"\n[{product_name}] Scraping {city}...")
            leads = scrape_product(product_cfg["keywords"], city, LEADS_PER_PRODUCT)
            print(f"  Actionable leads found: {len(leads)}")

            if not leads:
                per_product_counts[product_name] = 0
            else:
                rows = [format_lead_row(l, product_name, city) for l in leads]
                added = append_leads(SHEET_ID, product_cfg["tab"], SHEET_HEADERS, rows)
                per_product_counts[product_name] = added
                total_added += added
                print(f"  Added to sheet: {added}")

            # Send progress email if 15 minutes have elapsed since last notification
            now = time.time()
            if now - last_progress_notify >= PROGRESS_INTERVAL and idx < total_products:
                elapsed_min = int((now - run_start) / 60)
                try:
                    notify_progress_update(city, idx, total_products, total_added, elapsed_min)
                    last_progress_notify = now
                except Exception as e:
                    print(f"[NOTIFY WARN] Progress notification failed: {e}")

            time.sleep(2)

        advance_city(state, TIER1_CITIES, TIER2_CITIES)
        new_state = load_state()

        if not was_tier1_exhausted and new_state.get("exhausted_tier1"):
            print("\n[NOTIFY] Tier 1 exhausted — sending email")
            try:
                notify_tier1_exhausted()
            except Exception as e:
                print(f"[NOTIFY WARN] Tier 1 alert skipped: {e}")

        if not was_tier2_exhausted and new_state.get("exhausted_tier2"):
            print("\n[NOTIFY] Tier 2 exhausted — sending email")
            try:
                notify_tier2_exhausted()
            except Exception as e:
                print(f"[NOTIFY WARN] Tier 2 alert skipped: {e}")

        notify_daily_summary(city, total_added, per_product_counts)

        print(f"\n=== Done. Total leads added today: {total_added} ===\n")
        # A completed run with no new leads is still successful; duplicates or
        # temporarily empty search results should not fail the scheduled job.
        return 0
    finally:
        scraper_browser.close()


if __name__ == "__main__":
    sys.exit(main())
