"""
ExportersIndia scraper — Playwright-based, tertiary lead source.
Good coverage for Indian B2B suppliers, contractors, dealers.
Full phone numbers shown without login.
"""
import re
import time
from scrapers.browser import get_page

PHONE_RE = re.compile(r"[6-9]\d{9}")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def search(keyword: str, city: str, max_results: int = 20) -> list:
    leads = []
    seen_phones = set()

    page = get_page()

    # Try two URL variants
    urls = [
        f"https://www.exportersindia.com/search.php?ss={keyword.replace(' ', '+')}&searchtype=Sellers&city={city}",
        f"https://www.exportersindia.com/search.php?ss={keyword.replace(' ', '+')}+{city}&searchtype=Sellers",
    ]

    cards = []
    for url in urls:
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)

            for selector in [
                ".result-listing-item",
                ".seller-listing-item",
                ".company-list-item",
                ".search-result-item",
                ".listing-item",
                "li.s_list",
                ".sellerInfo",
                ".biz-listing",
            ]:
                found = page.query_selector_all(selector)
                real = [c for c in found if len(c.inner_text().strip()) > 30]
                if real:
                    cards = real
                    break

            if cards:
                break
        except Exception:
            continue

    if not cards:
        print(f"  [ExportersIndia] No listings found for {keyword} in {city}")
        return leads

    for card in cards[:max_results]:
        try:
            text = card.inner_text()
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
            if not lines:
                continue

            # Company name — try selectors, fall back to first line
            company = ""
            for sel in ["h2 a", "h3 a", ".company-name a", ".biz-name a", "h2", "h3", ".name"]:
                el = card.query_selector(sel)
                if el:
                    company = el.inner_text().strip()
                    if company:
                        break
            if not company:
                company = lines[0]
            if not company:
                continue

            # Phone — tel link first, then regex in text
            phone = ""
            tel = card.query_selector("a[href^='tel:']")
            if tel:
                raw = (tel.get_attribute("href") or "").replace("tel:", "").strip()
                phone = _clean_phone(raw)

            if not phone:
                for ln in lines:
                    m = PHONE_RE.search(re.sub(r"[^\d]", " ", ln))
                    if m:
                        candidate = _clean_phone(m.group())
                        if candidate:
                            phone = candidate
                            break

            if not phone:
                continue
            if phone in seen_phones:
                continue
            seen_phones.add(phone)

            # Email
            email = ""
            em = EMAIL_RE.search(text)
            if em:
                candidate = em.group()
                if not any(x in candidate.lower() for x in ["exportersindia", "example", "noreply"]):
                    email = candidate

            # Website
            website = ""
            for lnk in card.query_selector_all("a[href]"):
                href = lnk.get_attribute("href") or ""
                if href.startswith("http") and "exportersindia" not in href and "google" not in href:
                    website = href.split("?")[0]
                    break

            leads.append({
                "company": company,
                "contact_person": "",
                "phone": phone,
                "email": email,
                "designation": "",
                "website": website,
                "source": "ExportersIndia",
            })

        except Exception:
            continue

    print(f"  [ExportersIndia] {len(leads)} leads — {keyword} in {city}")
    time.sleep(1)
    return leads
