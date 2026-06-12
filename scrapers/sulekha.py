"""
Sulekha scraper — secondary source using Playwright.
Sulekha has strong coverage for service contractors and dealers.
Gets phone from listing; email from profile page.
"""
import re
import time
from scrapers.browser import get_page
from enricher import enrich_website

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
    page = get_page()
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

    page = get_page()
    working_url = None

    for url in candidate_urls:
        try:
            page.goto(url, timeout=30000, wait_until="commit")
            page.wait_for_timeout(3000)
            cards = page.query_selector_all(".sk-card")
            real_cards = [c for c in cards if len(c.inner_text().strip()) > 20]
            if real_cards:
                working_url = url
                break
        except Exception:
            continue

    if not working_url:
        return leads

    cards = page.query_selector_all(".sk-card")
    cards = [c for c in cards if len(c.inner_text().strip()) > 20]

    seen_phones = set()

    for card in cards[:max_results]:
        try:
            # Company name
            name_el = card.query_selector(".business .name a h3")
            if not name_el:
                name_el = card.query_selector(".business .name a")
            company = name_el.inner_text().strip() if name_el else ""
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
            profile_link = card.query_selector(".business .name a[href*='/profile/']")
            profile_url = profile_link.get_attribute("href") if profile_link else ""

            if not phone:
                continue
            if phone in seen_phones:
                continue
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

            # Fallback enrichment from company website
            if website and not email:
                web_data = enrich_website(website)
                email = web_data.get("email", "")
                if not contact_person:
                    contact_person = web_data.get("contact_person", "")

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
