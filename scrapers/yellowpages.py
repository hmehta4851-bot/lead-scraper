"""
YellowPages India scraper — free, no API key.
Major Indian business directory; good coverage of SMBs with phone numbers.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

PHONE_RE = re.compile(r"[6-9]\d{9}")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def search(keyword: str, city: str, max_results: int = 15) -> list:
    leads = []
    seen_phones: set = set()
    seen_companies: set = set()

    url = (
        f"http://www.yellowpages.in/search"
        f"?keyword={quote_plus(keyword)}&city={quote_plus(city)}"
    )

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  [YellowPages] HTTP {resp.status_code}")
            raise RuntimeError(f"YellowPages HTTP {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        listings = (
            soup.select("ul.search-results li")
            or soup.select(".listing-detail")
            or soup.select(".business-list > li")
            or soup.select("article")
            or soup.select("li.b_result")
        )

        for listing in listings[:max_results + 5]:
            if len(leads) >= max_results:
                break
            try:
                name_el = (
                    listing.select_one("h2 a")
                    or listing.select_one("h3 a")
                    or listing.select_one(".business-name")
                    or listing.select_one(".company-name")
                    or listing.select_one("h2")
                    or listing.select_one("h3")
                )
                company = (name_el.get_text(strip=True) if name_el else "").strip()
                if not company or len(company) < 3:
                    continue

                company_key = company.lower()[:50]
                if company_key in seen_companies:
                    continue

                # tel: href is most reliable phone source
                phone = ""
                tel_el = listing.select_one("a[href^='tel:']")
                if tel_el:
                    phone = _clean_phone(tel_el.get("href", "").replace("tel:", ""))

                if not phone:
                    raw_phones = PHONE_RE.findall(
                        re.sub(r"[\s\-]", "", listing.get_text(" "))
                    )
                    for rp in raw_phones:
                        p = _clean_phone(rp)
                        if p and re.match(r"[6-9]\d{9}$", p) and p not in seen_phones:
                            phone = p
                            break

                link_el = listing.select_one(
                    "a[href^='http']:not([href*='yellowpages'])"
                )
                website = (link_el.get("href", "") if link_el else "").strip()

                if not phone and not website:
                    continue
                if phone and phone in seen_phones:
                    continue

                seen_companies.add(company_key)
                if phone:
                    seen_phones.add(phone)

                leads.append({
                    "company": company,
                    "contact_person": "",
                    "phone": phone,
                    "email": "",
                    "designation": "",
                    "website": website,
                    "source": "YellowPages",
                })

            except Exception:
                continue

        print(f"  [YellowPages] {len(leads)} results — {keyword} in {city}")
        time.sleep(1)

    except Exception as e:
        print(f"  [YellowPages] Error: {e}")
        raise

    return leads
