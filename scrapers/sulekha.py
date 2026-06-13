"""
Sulekha scraper — secondary source using Playwright.
Sulekha has strong coverage for service contractors and dealers.
Gets phone from listing; email from profile page.
"""
import re
import time
from scrapers.browser import get_page

PHONE_RE = re.compile(r"[6-9]\d{9}")
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

CONTACT_PATTERNS = [
    re.compile(r"led by ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+)", re.I),
    re.compile(r"owned by ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+)", re.I),
    re.compile(r"managed by ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+)", re.I),
    re.compile(r"founder[, ]+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+)", re.I),
    re.compile(r"(?:Mr|Mrs|Ms|Dr)\.?\s+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+)", re.I),
    re.compile(r"proprietor[, ]+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+)", re.I),
    re.compile(r"director[, ]+([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)+)", re.I),
]

DESIGNATION_RE = re.compile(
    r"\b(Proprietor|Owner|Director|CEO|MD|Manager|Partner|Founder|Chairman)\b", re.I
)


def _slugify(text: str) -> str:
    return re.sub(r"\s+", "-", text.strip().lower())


def _get_profile_data(profile_url: str) -> dict:
    page = get_page("SulekhaProfile")
    result = {"email": "", "contact_person": "", "designation": "", "website": ""}
    try:
        page.goto(profile_url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        body = page.inner_text("body")

        emails = EMAIL_RE.findall(body)
        for em in emails:
            if not any(x in em.lower() for x in ["example", "sulekha", "@s.", "noreply"]):
                result["email"] = em
                break

        # Extract contact person from About section
        for pat in CONTACT_PATTERNS:
            m = pat.search(body)
            if m:
                result["contact_person"] = m.group(1).strip()
                break

        # Extract designation
        dm = DESIGNATION_RE.search(body)
        if dm:
            result["designation"] = dm.group(1).capitalize()

        # Try to get website
        links = page.query_selector_all("a[href]")
        for lnk in links:
            href = lnk.get_attribute("href") or ""
            if href.startswith("http") and "sulekha" not in href and "google" not in href and len(href) > 15:
                result["website"] = href.split("?")[0]
                break

    except Exception:
        pass
    return result


def search(keyword: str, city: str, max_results: int = 15) -> list:
    leads = []
    kw_slug = _slugify(keyword)
    city_slug = _slugify(city)

    # Try two URL variants: exact slug and with 's' suffix
    candidate_urls = [
        f"https://www.sulekha.com/{kw_slug}/{city_slug}",
        f"https://www.sulekha.com/{kw_slug}s/{city_slug}",
    ]

    # Selectors tried in order — Sulekha periodically renames CSS classes
    _CARD_SELECTORS = [
        ".sk-card",
        ".listingCard",
        "article.listing",
        ".searchResultsInfo li",
        ".listing-item",
        "[class*='card'][class*='listing']",
        "[class*='listingCard']",
        "[class*='sk-card']",
        "li[class*='result']",
    ]

    page = get_page("Sulekha")
    working_url = None
    cards = []

    for url in candidate_urls:
        try:
            page.goto(url, timeout=30000, wait_until="commit")
            page.wait_for_timeout(3000)
            for sel in _CARD_SELECTORS:
                found = page.query_selector_all(sel)
                real = [c for c in found if len(c.inner_text().strip()) > 20]
                if real:
                    cards = real
                    working_url = url
                    break
            if working_url:
                break
        except Exception:
            continue

    if not working_url or not cards:
        print(f"  [Sulekha] No listings found — {kw_slug}/{city_slug}")
        return leads

    # Convert DOM handles to plain data before profile navigation. This keeps
    # every listing valid even if the profile page changes navigation state.
    listing_data = []
    for card in cards[:max_results]:
        try:
            # Company name — try multiple selectors, fall back to first non-empty line
            company = ""
            for name_sel in [
                ".business .name a h3", ".business .name a", ".business-name a",
                "h2 a", "h3 a", "h2", "h3", "[class*='name'] a", "[class*='name']",
            ]:
                el = card.query_selector(name_sel)
                if el:
                    t = el.inner_text().strip()
                    if t:
                        company = t
                        break
            if not company:
                # last resort: first non-empty line of card text
                for ln in card.inner_text().splitlines():
                    ln = ln.strip()
                    if len(ln) > 3:
                        company = ln
                        break
            if not company:
                continue

            # Phone from tel: link
            phone = ""
            tel_link = card.query_selector("a[href^='tel:']")
            if tel_link:
                raw = (tel_link.get_attribute("href") or "").replace("tel:", "").strip()
                digits = re.sub(r"\D", "", raw)
                if digits.startswith("0"):
                    digits = digits[1:]
                if len(digits) >= 10:
                    phone = digits[-10:]

            # Fallback: regex in card text
            if not phone:
                m = PHONE_RE.search(card.inner_text())
                if m:
                    phone = m.group()

            # Profile URL
            profile_link = None
            for selector in (
                "a[href*='/profile/']",
                ".business .name a[href]",
                "h2 a[href]",
                "h3 a[href]",
            ):
                profile_link = card.query_selector(selector)
                if profile_link:
                    break
            profile_url = profile_link.get_attribute("href") if profile_link else ""

            if not phone:
                continue
            listing_data.append(
                {
                    "company": company,
                    "phone": phone,
                    "profile_url": profile_url,
                }
            )
        except Exception:
            continue

    seen_phones = set()
    for listing in listing_data:
        try:
            company = listing["company"]
            phone = listing["phone"]
            profile_url = listing["profile_url"]
            if phone and phone in seen_phones:
                continue
            if phone:
                seen_phones.add(phone)

            # Get email + contact from profile page
            enriched = {}
            if profile_url:
                enriched = _get_profile_data(profile_url)
                time.sleep(0.5)

            email = enriched.get("email", "")
            contact_person = enriched.get("contact_person", "")
            designation = enriched.get("designation", "")
            website = enriched.get("website", "")

            leads.append(
                {
                    "company": company,
                    "contact_person": contact_person,
                    "phone": phone,
                    "email": email,
                    "designation": designation,
                    "website": website,
                    "source": "Sulekha",
                }
            )

        except Exception:
            continue

    return leads
