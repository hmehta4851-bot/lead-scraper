"""
IndiaMART scraper — Playwright + Next.js __NEXT_DATA__ extraction.
Phone numbers are partially masked on listing pages (requires login for full number).
This scraper falls back to [] gracefully if masking is detected.
Kept as optional quaternary source; don't count on it.
"""
import re
import json
import time
from scrapers.browser import get_page

MASK_RE = re.compile(r"X{3,}|x{3,}|\*{3,}")
PHONE_RE = re.compile(r"[6-9]\d{9}")


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def _walk_for_companies(obj, depth=0):
    """Recursively search Next.js data for company list arrays."""
    if depth > 8:
        return []
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        # Check if this looks like a company list
        first = obj[0]
        if any(k in first for k in ["company_name", "companyName", "COMPANY_NAME"]):
            return obj
    if isinstance(obj, dict):
        for val in obj.values():
            result = _walk_for_companies(val, depth + 1)
            if result:
                return result
    return []


def search(keyword: str, city: str, max_results: int = 25) -> list:
    leads = []
    seen_phones = set()

    query = f"{keyword} {city}"
    url = f"https://www.indiamart.com/search.mp?ss={query.replace(' ', '+')}&f=&prdsrc=1"

    page = get_page()
    try:
        page.goto(url, timeout=35000, wait_until="commit")
        page.wait_for_timeout(4000)

        script = page.query_selector("script#__NEXT_DATA__")
        if not script:
            return leads

        try:
            data = json.loads(script.inner_text())
        except Exception:
            return leads

        companies = _walk_for_companies(data)
        if not companies:
            return leads

        unmasked_count = 0
        for item in companies[:max_results]:
            if not isinstance(item, dict):
                continue
            try:
                company = (
                    item.get("company_name", "")
                    or item.get("companyName", "")
                    or item.get("COMPANY_NAME", "")
                    or ""
                ).strip()
                if not company:
                    continue

                phone_raw = str(
                    item.get("phone_no", "")
                    or item.get("mobile", "")
                    or item.get("phoneNo", "")
                    or item.get("MOBILE_NO", "")
                    or ""
                )

                # Skip if masked
                if MASK_RE.search(phone_raw):
                    continue

                phone = _clean_phone(phone_raw)
                if not phone or not re.match(r"[6-9]\d{9}", phone):
                    continue
                if phone in seen_phones:
                    continue
                seen_phones.add(phone)
                unmasked_count += 1

                email = (
                    item.get("email_id", "")
                    or item.get("email", "")
                    or item.get("EMAIL_ID", "")
                    or ""
                ).strip()
                website = (
                    item.get("website", "")
                    or item.get("websiteUrl", "")
                    or item.get("WEB_SITE", "")
                    or ""
                ).strip()
                if website and not website.startswith("http"):
                    website = "https://" + website
                contact_person = (
                    item.get("contact_person", "")
                    or item.get("personName", "")
                    or item.get("PERSON_NAME", "")
                    or ""
                ).strip()
                designation = (
                    item.get("designation", "")
                    or item.get("DESIGNATION", "")
                    or ""
                ).strip()

                leads.append({
                    "company": company,
                    "contact_person": contact_person,
                    "phone": phone,
                    "email": email,
                    "designation": designation,
                    "website": website,
                    "source": "IndiaMART",
                })

            except Exception:
                continue

        if unmasked_count == 0 and companies:
            print(f"  [IndiaMART] Phones masked (login required) — skipping")
        else:
            print(f"  [IndiaMART] {len(leads)} leads — {keyword} in {city}")

        time.sleep(1)

    except Exception as e:
        print(f"  [IndiaMART] Error: {e}")

    return leads
