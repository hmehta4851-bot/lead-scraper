"""Autonomous, vertical-first lead collection for Sunzone Sports & Play."""

from __future__ import annotations

import re
import sys
import time
from collections import Counter
from datetime import date
from urllib.parse import urlparse

from config import (
    KEYWORDS_PER_PRODUCT_PER_RUN,
    LEADS_PER_PRODUCT,
    MAX_LEADS_PER_SOURCE_PER_VERTICAL,
    SHEET_HEADERS,
    SHEET_ID,
    SOURCE_LEAD_CAP,
    SOURCE_RESULT_LIMIT,
    TARGET_LEADS_PER_VERTICAL,
    TIER1_CITIES,
    TIER2_CITIES,
    iter_products,
)
from enricher import enrich_website, resolve_contact_names
from keyword_library import add_buyer_intent, cursor_key, select_rotating_keywords
from qualification import competitor_reasons, qualify_lead
from notifier import (
    notify_daily_summary,
    notify_progress_update,
    notify_scraper_started,
    notify_tier1_exhausted,
    notify_tier2_exhausted,
)
from scrapers import (
    bing,
    duckduckgo,
    exportersindia,
    googlemaps,
    indiamart,
    justdial,
    openstreetmap,
    sulekha,
    tradeindia,
    yahoo,
    yellowpages,
)
from scrapers import browser as scraper_browser
from sheets import append_leads, load_existing_phones
from state import advance_city, get_today_city, load_state, save_state


SOURCE_REGISTRY = (
    ("Sulekha", sulekha.search),
    ("ExportersIndia", exportersindia.search),
    ("TradeIndia", tradeindia.search),
    ("DuckDuckGo", duckduckgo.search),
    ("Bing", bing.search),
    ("YellowPages", yellowpages.search),
    ("OpenStreetMap", openstreetmap.search),
    ("Yahoo", yahoo.search),
    ("IndiaMART", indiamart.search),
    ("JustDial", justdial.search),
    ("Google Maps", googlemaps.search),
)

_OWN_BRAND_RE = re.compile(
    r"\bsunzone\b|\bsunzone\.in\b|\bsunzonesport(?:s)?\b",
    re.I,
)
_COMPANY_NOISE_RE = re.compile(
    r"\b(pvt\.?\s*ltd\.?|private\s+limited|limited|llp|inc\.?|india|co\.)\b",
    re.I,
)


def _lead_identity_text(lead: dict) -> str:
    website = str(lead.get("website", ""))
    email = str(lead.get("email", ""))
    host = urlparse(
        website if "://" in website else f"https://{website}"
    ).netloc
    return " ".join(
        (
            str(lead.get("company", "")),
            website,
            host,
            email.partition("@")[2],
        )
    )


def is_own_brand(lead: dict) -> bool:
    return bool(_OWN_BRAND_RE.search(_lead_identity_text(lead)))


def is_competitor(lead: dict) -> bool:
    return bool(competitor_reasons(lead))


def is_actionable_lead(lead: dict) -> bool:
    """Accept contactable prospects while excluding our own and competitors."""
    if not str(lead.get("company", "")).strip():
        return False
    if not str(lead.get("phone", "")).strip():
        return False
    return not is_own_brand(lead) and not is_competitor(lead)


def _lead_score(lead: dict) -> int:
    score = 35
    if lead.get("phone"):
        score += 25
    if lead.get("email"):
        score += 15
    if lead.get("contact_person"):
        score += 10
    if lead.get("website"):
        score += 10
    if lead.get("designation"):
        score += 5
    return min(score, 100)


def _norm_phone(value: str) -> str:
    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def _norm_company(name: str) -> str:
    normalized = _COMPANY_NOISE_RE.sub("", name.lower()).strip()
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()[:80]


def run_all_sources(keyword: str, city: str) -> tuple[list[dict], dict]:
    """Attempt every configured source; one failure never blocks another."""
    leads: list[dict] = []
    telemetry = {"attempted": [], "failed": {}, "raw_counts": {}}
    for source_name, search in SOURCE_REGISTRY:
        telemetry["attempted"].append(source_name)
        print(f"  [{source_name}] {keyword} in {city}")
        try:
            found = search(keyword, city, max_results=SOURCE_RESULT_LIMIT) or []
            for lead in found:
                lead.setdefault("source", source_name)
                lead["search_keyword"] = keyword
            leads.extend(found)
            telemetry["raw_counts"][source_name] = len(found)
            print(f"  [{source_name}] +{len(found)} raw")
        except Exception as exc:
            telemetry["failed"][source_name] = f"{type(exc).__name__}: {exc}"
            telemetry["raw_counts"][source_name] = 0
            print(f"  [{source_name}] FAILED: {exc}")
        time.sleep(0.5)
    return leads, telemetry


def _deduplicate(raw_leads: list[dict]) -> list[dict]:
    seen_phones: set[str] = set()
    seen_companies: set[str] = set()
    output: list[dict] = []
    for lead in raw_leads:
        phone = _norm_phone(str(lead.get("phone", "")))
        company = _norm_company(str(lead.get("company", "")))
        if phone:
            lead["phone"] = phone
            if phone in seen_phones:
                continue
            seen_phones.add(phone)
        elif lead.get("website") and company:
            if company in seen_companies:
                continue
            seen_companies.add(company)
        else:
            continue
        output.append(lead)
    return output


def _enrich(leads: list[dict], seen_phones: set[str], limit: int) -> None:
    candidates = [
        lead for lead in leads
        if lead.get("website")
        and (
            not lead.get("phone")
            or not lead.get("email")
            or not lead.get("contact_person")
        )
    ]
    for lead in candidates[:limit]:
        try:
            enriched = enrich_website(lead["website"], max_pages=2)
            phone = _norm_phone(enriched.get("phone", ""))
            if phone and phone not in seen_phones and not lead.get("phone"):
                lead["phone"] = phone
                seen_phones.add(phone)
            for field in ("email", "contact_person", "designation"):
                if enriched.get(field) and not lead.get(field):
                    lead[field] = enriched[field]
            if enriched.get("website_text"):
                lead["website_text"] = enriched["website_text"]
        except Exception as exc:
            print(f"  [Enricher] {lead.get('website')} skipped: {exc}")


def scrape_product(
    keyword_list: list[str],
    city: str,
    vertical: str,
    target: int = LEADS_PER_PRODUCT,
    source_counts: Counter | None = None,
) -> tuple[list[dict], list[dict]]:
    all_raw: list[dict] = []
    source_runs: list[dict] = []
    for keyword in keyword_list:
        raw, telemetry = run_all_sources(keyword, city)
        all_raw.extend(raw)
        source_runs.append({"keyword": keyword, **telemetry})

    deduped = _deduplicate(all_raw)
    seen_phones = {
        lead["phone"] for lead in deduped if lead.get("phone")
    }
    _enrich(deduped, seen_phones, limit=60)

    actionable = []
    for lead in deduped:
        if is_own_brand(lead):
            continue
        qualified, score, reason = qualify_lead(lead, vertical)
        if not qualified:
            continue
        lead["lead_score"] = score
        lead["qualification_reason"] = reason
        actionable.append(lead)
    actionable.sort(
        key=lambda lead: (
            int(lead.get("lead_score", 0)),
            _lead_score(lead),
        ),
        reverse=True,
    )

    buckets: dict[str, list[dict]] = {}
    source_counts = source_counts or Counter()
    for lead in actionable:
        source = lead.get("source", "Unknown")
        bucket = buckets.setdefault(source, [])
        available = min(
            SOURCE_LEAD_CAP,
            max(
                0,
                MAX_LEADS_PER_SOURCE_PER_VERTICAL - source_counts[source],
            ),
        )
        if len(bucket) < available:
            bucket.append(lead)

    # Round-robin selection gives every productive source a fair chance while
    # preserving quality order within each source.
    selected: list[dict] = []
    source_names = list(buckets)
    offset = 0
    while len(selected) < target:
        added_this_round = False
        for source in source_names:
            bucket = buckets[source]
            if offset < len(bucket):
                selected.append(bucket[offset])
                added_this_round = True
                if len(selected) >= target:
                    break
        if not added_this_round:
            break
        offset += 1

    _enrich(selected, seen_phones, limit=20)
    try:
        resolve_contact_names(selected, city)
    except Exception as exc:
        print(f"  [Contact resolver] skipped: {exc}")
    return selected, source_runs


def format_lead_row(
    lead: dict,
    vertical: str,
    product: str,
    city: str,
) -> dict:
    return {
        "Date": str(date.today()),
        "City": city,
        "Vertical": vertical,
        "Product": product,
        "Search Keyword": lead.get("search_keyword", ""),
        "Company Name": lead.get("company", ""),
        "Contact Person": lead.get("contact_person", ""),
        "Phone": lead.get("phone", ""),
        "Email": lead.get("email", ""),
        "Designation": lead.get("designation", ""),
        "Source": lead.get("source", ""),
        "Website": lead.get("website", ""),
        "Lead Score": lead.get("lead_score", _lead_score(lead)),
        "Qualification Reason": lead.get("qualification_reason", ""),
    }


def apply_vertical_source_caps(
    leads: list[dict],
    source_counts: Counter,
    cap: int = MAX_LEADS_PER_SOURCE_PER_VERTICAL,
) -> list[dict]:
    """Prevent any one source from dominating a vertical's daily output."""
    accepted: list[dict] = []
    provisional = Counter(source_counts)
    for lead in leads:
        source = str(lead.get("source") or "Unknown")
        if provisional[source] >= cap:
            continue
        accepted.append(lead)
        provisional[source] += 1
    return accepted


def main() -> int:
    try:
        state = load_state()
        city = get_today_city(state, TIER1_CITIES, TIER2_CITIES)
        products = list(iter_products())
        print(
            f"\n=== Sunzone Lead Scraper | {date.today()} | "
            f"{city} | Tier {state['tier']} ===\n"
        )

        per_product_counts: dict[str, int] = {}
        per_source_counts: dict[str, int] = {}
        quality_stats = {
            "with_email": 0,
            "with_contact": 0,
            "with_website": 0,
            "with_phone": 0,
        }
        total_added = 0
        vertical_counts: Counter = Counter()
        vertical_source_counts: dict[str, Counter] = {
            vertical: Counter() for vertical, _, _, _ in products
        }
        source_failures: Counter = Counter()
        started = time.time()
        last_progress = started
        vertical_tabs = list(dict.fromkeys(tab for _, tab, _, _ in products))
        existing_phones = load_existing_phones(SHEET_ID, vertical_tabs)
        print(
            f"[SHEET] Loaded {len(existing_phones)} existing phone numbers "
            "for global duplicate protection"
        )

        try:
            notify_scraper_started(city, len(products))
        except Exception as exc:
            print(f"[NOTIFY WARN] Start notification failed: {exc}")

        for index, (vertical, tab, product, fallback) in enumerate(products, 1):
            if vertical_counts[vertical] >= TARGET_LEADS_PER_VERTICAL:
                print(
                    f"\n[{vertical}] Daily target reached "
                    f"({vertical_counts[vertical]}); remaining products skipped"
                )
                continue
            print(f"\n[{vertical} / {product}] Scraping {city}...")
            cursors = state.setdefault("keyword_cursors", {})
            keywords, next_cursor = select_rotating_keywords(
                vertical,
                product,
                fallback,
                cursors,
                KEYWORDS_PER_PRODUCT_PER_RUN,
                city,
            )
            buyer_cursors = state.setdefault("buyer_cursors", {})
            product_cursor_key = cursor_key(vertical, product)
            buyer_cursor = int(buyer_cursors.get(product_cursor_key, 0))
            keywords = add_buyer_intent(
                vertical,
                keywords,
                buyer_cursor,
            )
            if not keywords:
                print("  [WARN] No keywords configured; skipping")
                per_product_counts[product] = 0
                continue

            try:
                remaining = TARGET_LEADS_PER_VERTICAL - vertical_counts[vertical]
                leads, runs = scrape_product(
                    keywords,
                    city,
                    vertical,
                    min(LEADS_PER_PRODUCT, remaining),
                    vertical_source_counts[vertical],
                )
                for run in runs:
                    source_failures.update(run["failed"])
            except Exception as exc:
                print(f"  [ERROR] Product failed safely: {exc}")
                per_product_counts[product] = 0
                continue

            leads = apply_vertical_source_caps(
                leads,
                vertical_source_counts[vertical],
            )
            rows = [
                format_lead_row(lead, vertical, product, city)
                for lead in leads
            ]
            try:
                written_rows = append_leads(
                    SHEET_ID,
                    tab,
                    SHEET_HEADERS,
                    rows,
                    existing_phones=existing_phones,
                )
                added = len(written_rows)
            except Exception as exc:
                print(f"  [ERROR] Sheet write failed safely: {exc}")
                written_rows = []
                added = 0

            per_product_counts[product] = added
            total_added += added
            vertical_counts[vertical] += added
            for row in written_rows:
                source = row.get("Source", "Unknown")
                per_source_counts[source] = per_source_counts.get(source, 0) + 1
                vertical_source_counts[vertical][source] += 1
                quality_stats["with_phone"] += bool(row.get("Phone"))
                quality_stats["with_email"] += bool(row.get("Email"))
                quality_stats["with_contact"] += bool(row.get("Contact Person"))
                quality_stats["with_website"] += bool(row.get("Website"))

            cursors[cursor_key(vertical, product)] = next_cursor
            buyer_cursors[product_cursor_key] = buyer_cursor + len(keywords)
            save_state(state)
            print(
                f"  Keywords: {', '.join(keywords)} | "
                f"actionable: {len(leads)} | added: {added}"
            )

            now = time.time()
            if now - last_progress >= 10 * 60 and index < len(products):
                try:
                    notify_progress_update(
                        city,
                        index,
                        len(products),
                        total_added,
                        int((now - started) / 60),
                    )
                    last_progress = now
                except Exception as exc:
                    print(f"[NOTIFY WARN] Progress notification failed: {exc}")

        advance_city(state, TIER1_CITIES, TIER2_CITIES)
        new_state = load_state()
        if new_state.get("last_transition") == "tier1_to_tier2":
            try:
                notify_tier1_exhausted()
            except Exception as exc:
                print(f"[NOTIFY WARN] Tier 1 alert failed: {exc}")
        if new_state.get("last_transition") == "tier2_to_tier1":
            try:
                notify_tier2_exhausted()
            except Exception as exc:
                print(f"[NOTIFY WARN] Tier 2 alert failed: {exc}")

        duration = int((time.time() - started) / 60)
        try:
            notify_daily_summary(
                city,
                total_added,
                per_product_counts,
                per_source_counts,
                quality_stats,
                duration,
                dict(source_failures),
            )
        except Exception as exc:
            print(f"[NOTIFY WARN] Summary notification failed: {exc}")

        print(f"\nSource failures (isolated): {dict(source_failures)}")
        print(f"=== Done. New unique leads: {total_added} ===\n")
        return 0
    finally:
        scraper_browser.close()


if __name__ == "__main__":
    sys.exit(main())
