"""
JustDial scraper — India's largest local business directory.
Uses requests with mobile user-agent to reduce bot detection.
Phone numbers checked via data-phone attribute, tel: href, and text scan.
Falls back gracefully to empty list if blocked.
"""
import re
import time
import requests
from bs4 import BeautifulSoup

PHONE_RE = re.compile(r"[6-9]\d{9}")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.google.com/",
}


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def search(keyword: str, city: str, max_results: int = 20) -> list:
    leads = []
    seen_phones: set = set()
    seen_companies: set = set()

    kw_slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower().strip()).strip("-")
    city_name = city.split(",", 1)[0].strip()
    city_slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        city_name.lower(),
    ).strip("-")
    url = f"https://www.justdial.com/{city_slug}/{kw_slug}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  [JustDial] HTTP {resp.status_code} — skipped")
            raise RuntimeError(f"JustDial HTTP {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        listings = (
            soup.select("li.cntanr")
            or soup.select("li[data-id]")
            or soup.select(".resultbox_info")
            or soup.select("article.item")
            or soup.select("li[class*='result']")
        )

        for listing in listings[:max_results + 5]:
            if len(leads) >= max_results:
                break
            try:
                name_el = (
                    listing.select_one("span.lng")
                    or listing.select_one("h2.jcn")
                    or listing.select_one(".store-name")
                    or listing.select_one("h2")
                    or listing.select_one("h3")
                )
                company = (name_el.get_text(strip=True) if name_el else "").strip()
                if not company or len(company) < 3:
                    continue

                company_key = company.lower()[:50]
                if company_key in seen_companies:
                    continue

                phone = ""

                # data-phone attribute (JD sometimes stores encoded number here)
                phone_el = listing.select_one("[data-phone]")
                if phone_el:
                    raw = phone_el.get("data-phone", "")
                    phone = _clean_phone(raw)
                    if not re.match(r"[6-9]\d{9}$", phone):
                        phone = ""

                # tel: href
                if not phone:
                    tel_el = listing.select_one("a[href^='tel:']")
                    if tel_el:
                        phone = _clean_phone(tel_el.get("href", "").replace("tel:", ""))

                # text scan
                if not phone:
                    raw_phones = PHONE_RE.findall(
                        re.sub(r"[\s\-]", "", listing.get_text(" "))
                    )
                    for rp in raw_phones:
                        p = _clean_phone(rp)
                        if p and re.match(r"[6-9]\d{9}$", p):
                            phone = p
                            break

                if not phone or phone in seen_phones:
                    continue

                seen_companies.add(company_key)
                seen_phones.add(phone)

                leads.append({
                    "company": company,
                    "contact_person": "",
                    "phone": phone,
                    "email": "",
                    "designation": "",
                    "website": "",
                    "source": "JustDial",
                })

            except Exception:
                continue

        if leads:
            print(f"  [JustDial] {len(leads)} leads — {keyword} in {city}")
        else:
            print(f"  [JustDial] 0 leads (likely blocked) — {keyword} in {city}")
        time.sleep(1)

    except Exception as e:
        print(f"  [JustDial] Error: {e}")
        raise

    return leads
