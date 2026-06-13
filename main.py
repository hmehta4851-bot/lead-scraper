"""Autonomous, vertical-first lead collection for Sunzone Sports & Play."""

from __future__ import annotations

import re
import sys
import time
from collections import Counter
from datetime import date
from urllib.parse import urlparse

from config import (
    INDIA_CITY_ROTATION,
    KEYWORDS_PER_PRODUCT_PER_RUN,
    LEADS_PER_PRODUCT,
    MAX_CITIES_PER_DAY,
    MAX_LEADS_PER_SOURCE_PER_VERTICAL,
    MAX_RUN_MINUTES,
    MAX_SAME_CITY_ROUNDS,
    NO_PROGRESS_ROUNDS_BEFORE_NEXT_CITY,
    SHEET_HEADERS,
    SHEET_ID,
    SOURCE_LEAD_CAP,
    SOURCE_RESULT_LIMIT,
    TARGET_LEADS_PER_VERTICAL,
    iter_products,
)
from enricher import enrich_website, resolve_contact_names
from keyword_library import add_buyer_intent, cursor_key, select_rotating_keywords
from qualification import competitor_reasons, qualify_lead
from notifier import (
    notify_daily_summary,
    notify_progress_update,
    notify_scraper_started,
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
from sheets import append_leads, load_daily_snapshot
from state import complete_city_batch, get_scheduled_city, load_state, save_state


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

BUYER_SOURCE_REGISTRY = tuple(
    source
    for source in SOURCE_REGISTRY
    if source[0]
    in {
        "Sulekha",
        "DuckDuckGo",
        "Bing",
        "YellowPages",
        "OpenStreetMap",
        "Yahoo",
        "JustDial",
        "Google Maps",
    }
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


def run_all_sources(
    keyword: str,
    city: str,
    source_registry=None,
) -> tuple[list[dict], dict]:
    """Attempt every configured source; one failure never blocks another."""
    source_registry = source_registry or SOURCE_REGISTRY
    leads: list[dict] = []
    telemetry = {"attempted": [], "failed": {}, "raw_counts": {}}
    for source_name, search in source_registry:
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
    source_registry=None,
) -> tuple[list[dict], list[dict]]:
    source_registry = source_registry or SOURCE_REGISTRY
    all_raw: list[dict] = []
    source_runs: list[dict] = []
    for keyword in keyword_list:
        raw, telemetry = run_all_sources(
            keyword,
            city,
            source_registry=source_registry,
        )
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


def vertical_quotas_met(
    vertical_counts: Counter | dict[str, int],
    verticals,
    target: int = TARGET_LEADS_PER_VERTICAL,
) -> bool:
    """Fail closed unless every configured vertical reaches its target."""
    return all(vertical_counts.get(vertical, 0) >= target for vertical in verticals)


def main() -> int:
    try:
        state = load_state()
        run_date = date.today()
        if state.get("last_run_date") == str(run_date):
            print(
                f"Today's city batch is already complete: "
                f"{', '.join(state.get('last_run_cities') or [state.get('last_run_city', '')])}"
            )
            return 0
        start_index = int(state.get("city_index", 0)) % len(INDIA_CITY_ROTATION)
        city = get_scheduled_city(state, INDIA_CITY_ROTATION, run_date)
        products = list(iter_products())
        products_by_vertical: dict[str, list[tuple[str, str, list[str]]]] = {}
        for vertical, tab, product, fallback in products:
            products_by_vertical.setdefault(vertical, []).append(
                (tab, product, fallback)
            )
        print(
            f"\n=== Sunzone Lead Scraper | {run_date} | "
            f"{city} | National cycle {state['rotation_cycle']} ===\n"
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
        source_failures: Counter = Counter()
        started = time.time()
        deadline = started + (MAX_RUN_MINUTES * 60)
        last_progress = started
        vertical_tabs = list(dict.fromkeys(tab for _, tab, _, _ in products))
        (
            existing_phones,
            vertical_counts,
            snapshot_source_counts,
        ) = load_daily_snapshot(
            SHEET_ID,
            vertical_tabs,
            run_date,
            city=None,
        )
        vertical_source_counts: dict[str, Counter] = {
            vertical: Counter(snapshot_source_counts.get(vertical, {}))
            for vertical in products_by_vertical
        }
        print(
            f"[SHEET] Loaded {len(existing_phones)} existing phone numbers "
            "for global duplicate protection"
        )
        print(
            "[SHEET] Today's starting counts: "
            + ", ".join(
                f"{vertical}={vertical_counts[vertical]}"
                for vertical in products_by_vertical
            )
        )

        try:
            notify_scraper_started(city, len(products_by_vertical))
        except Exception as exc:
            print(f"[NOTIFY WARN] Start notification failed: {exc}")

        buyer_cursors = state.setdefault("buyer_cursors", {})
        for vertical in products_by_vertical:
            buyer_cursors.setdefault(vertical, 0)
        keyword_cursors = state.setdefault("keyword_cursors", {})

        operation = 0
        max_operations = (
            MAX_CITIES_PER_DAY
            * MAX_SAME_CITY_ROUNDS
            * len(products_by_vertical)
        )
        budget_exhausted = False
        used_cities = []
        for city_offset in range(MAX_CITIES_PER_DAY):
            if time.time() >= deadline or vertical_quotas_met(
                vertical_counts,
                products_by_vertical,
            ):
                budget_exhausted = time.time() >= deadline
                break
            city = INDIA_CITY_ROTATION[
                (start_index + city_offset) % len(INDIA_CITY_ROTATION)
            ]
            print(
                f"\n=== Daily town group {len(used_cities) + 1}/"
                f"{MAX_CITIES_PER_DAY}: {city} ==="
            )
            no_progress_rounds = 0
            for round_number in range(1, MAX_SAME_CITY_ROUNDS + 1):
                if time.time() >= deadline:
                    budget_exhausted = True
                    break
                if city not in used_cities:
                    used_cities.append(city)
                incomplete = [
                    vertical
                    for vertical in products_by_vertical
                    if vertical_counts[vertical] < TARGET_LEADS_PER_VERTICAL
                ]
                if not incomplete:
                    break
                print(
                    f"\n=== Keyword round {round_number}/"
                    f"{MAX_SAME_CITY_ROUNDS} in {city}: "
                    f"{', '.join(incomplete)} ==="
                )
                round_start_total = total_added
                for vertical in incomplete:
                    if time.time() >= deadline:
                        budget_exhausted = True
                        break
                    operation += 1
                    entries = products_by_vertical[vertical]
                    buyer_cursor = int(buyer_cursors.get(vertical, 0))
                    completed_queries = 0
                    for query_offset in range(KEYWORDS_PER_PRODUCT_PER_RUN):
                        if time.time() >= deadline:
                            budget_exhausted = True
                            break
                        if vertical_counts[vertical] >= TARGET_LEADS_PER_VERTICAL:
                            break
                        entry_index = (
                            buyer_cursor + query_offset
                        ) % len(entries)
                        tab, product, fallback = entries[entry_index]
                        selected, next_keyword_cursor = select_rotating_keywords(
                            vertical,
                            product,
                            fallback,
                            keyword_cursors,
                            count=1,
                            city=city,
                        )
                        if not selected:
                            continue
                        query = add_buyer_intent(
                            vertical,
                            selected,
                            buyer_cursor + query_offset,
                        )[0]
                        remaining = (
                            TARGET_LEADS_PER_VERTICAL - vertical_counts[vertical]
                        )
                        print(
                            f"\n[{vertical} / {product}] "
                            f"Buyer search: {query} in {city} | "
                            f"remaining: {remaining}"
                        )
                        try:
                            source_registry = (
                                SOURCE_REGISTRY
                                if round_number == 1
                                else BUYER_SOURCE_REGISTRY
                            )
                            leads, runs = scrape_product(
                                [query],
                                city,
                                vertical,
                                min(LEADS_PER_PRODUCT, remaining),
                                vertical_source_counts[vertical],
                                source_registry,
                            )
                            for run in runs:
                                source_failures.update(run["failed"])
                        except Exception as exc:
                            print(
                                f"  [ERROR] Buyer search failed safely: {exc}"
                            )
                            continue

                        leads = apply_vertical_source_caps(
                            leads,
                            vertical_source_counts[vertical],
                        )
                        rows = [
                            format_lead_row(
                                lead,
                                vertical,
                                product,
                                city,
                            )
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
                        except Exception as exc:
                            print(
                                f"  [ERROR] Sheet write failed safely: {exc}"
                            )
                            written_rows = []

                        added = len(written_rows)
                        per_product_counts[product] = (
                            per_product_counts.get(product, 0) + added
                        )
                        total_added += added
                        vertical_counts[vertical] += added
                        for row in written_rows:
                            source = row.get("Source", "Unknown")
                            per_source_counts[source] = (
                                per_source_counts.get(source, 0) + 1
                            )
                            vertical_source_counts[vertical][source] += 1
                            quality_stats["with_phone"] += bool(row.get("Phone"))
                            quality_stats["with_email"] += bool(row.get("Email"))
                            quality_stats["with_contact"] += bool(
                                row.get("Contact Person")
                            )
                            quality_stats["with_website"] += bool(
                                row.get("Website")
                            )
                        print(
                            f"  Query: {query} | actionable: {len(leads)} | "
                            f"added: {added} | "
                            f"{vertical}: {vertical_counts[vertical]}/"
                            f"{TARGET_LEADS_PER_VERTICAL}"
                        )
                        keyword_cursors[cursor_key(vertical, product)] = (
                            next_keyword_cursor
                        )
                        completed_queries += 1

                    buyer_cursors[vertical] = buyer_cursor + completed_queries
                    save_state(state)

                    now = time.time()
                    if now - last_progress >= 10 * 60:
                        try:
                            notify_progress_update(
                                city,
                                operation,
                                max_operations,
                                total_added,
                                int((now - started) / 60),
                            )
                            last_progress = now
                        except Exception as exc:
                            print(
                                f"[NOTIFY WARN] Progress notification failed: {exc}"
                            )

                if total_added == round_start_total:
                    no_progress_rounds += 1
                    if (
                        no_progress_rounds
                        >= NO_PROGRESS_ROUNDS_BEFORE_NEXT_CITY
                    ):
                        print(
                            f"[CITY GROUP] {city} added no new qualified "
                            "leads in a complete round; adding the next town."
                        )
                        break
                else:
                    no_progress_rounds = 0
            if budget_exhausted:
                break

        quotas_met = vertical_quotas_met(
            vertical_counts,
            products_by_vertical,
        )
        if not used_cities:
            used_cities = [city]
        complete_city_batch(
            state,
            INDIA_CITY_ROTATION,
            run_date,
            used_cities,
        )

        duration = int((time.time() - started) / 60)
        city_summary = (
            used_cities[0]
            if len(used_cities) == 1
            else f"{used_cities[0]} + {len(used_cities) - 1} towns"
        )
        try:
            notify_daily_summary(
                city_summary,
                total_added,
                per_product_counts,
                per_source_counts,
                quality_stats,
                duration,
                dict(source_failures),
                dict(vertical_counts),
                TARGET_LEADS_PER_VERTICAL,
                quotas_met,
            )
        except Exception as exc:
            print(f"[NOTIFY WARN] Summary notification failed: {exc}")

        print(f"\nSource failures (isolated): {dict(source_failures)}")
        if budget_exhausted:
            print(
                f"[RUNTIME] Safe {MAX_RUN_MINUTES}-minute keyword budget "
                "reached; remaining quotas are reported without lowering "
                "quality."
            )
        print(
            "[QUOTAS] "
            + ", ".join(
                f"{vertical}={vertical_counts[vertical]}/"
                f"{TARGET_LEADS_PER_VERTICAL}"
                for vertical in products_by_vertical
            )
        )
        print(f"=== Done. New unique leads: {total_added} ===\n")
        return 0 if quotas_met else 2
    finally:
        scraper_browser.close()


if __name__ == "__main__":
    sys.exit(main())
