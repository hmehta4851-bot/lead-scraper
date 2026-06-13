"""
DuckDuckGo HTML search scraper — 100% free, no API key, no rate limits.
Uses requests (not Playwright) to avoid shared-page conflicts.
Phone-less results passed to enricher.py to resolve contact details.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus

PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9](?:[\-\s]?\d){9}")

_SKIP_DOMAINS = {
    "google", "facebook", "youtube", "wikipedia", "amazon", "flipkart",
    "snapdeal", "indiamart", "tradeindia", "sulekha", "justdial",
    "exportersindia", "twitter", "linkedin", "instagram", "quora",
    "reddit", "olx", "99acres", "magicbricks", "housing",
}

_TITLE_STRIP_RE = re.compile(
    r"\s*[|\-–—]\s*.+$"
    r"|\s*(Pvt\.?|Ltd\.?|Private\s+Limited|India|Official\s+(Website|Site))\s*$",
    re.I,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def _skip_domain(url: str) -> bool:
    try:
        netloc = urlparse(url).netloc.lower().replace("www.", "")
        return any(skip in netloc for skip in _SKIP_DOMAINS)
    except Exception:
        return False


def search(keyword: str, city: str, max_results: int = 15) -> list:
    leads = []
    seen_phones: set = set()
    seen_companies: set = set()

    query = f"{keyword} {city} phone contact"
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  [DuckDuckGo] HTTP {resp.status_code}")
            return leads

        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.select(".result__body") or soup.select(".result")

        for result in results:
            if len(leads) >= max_results:
                break
            try:
                title_el = result.select_one(".result__a")
                snippet_el = result.select_one(".result__snippet")
                url_el = result.select_one(".result__url")

                title = (title_el.get_text(strip=True) if title_el else "").strip()
                snippet = (snippet_el.get_text(strip=True) if snippet_el else "").strip()
                result_url = (url_el.get_text(strip=True) if url_el else "").strip()

                if not title or len(title) < 5:
                    continue

                website = result_url.strip()
                if website and not website.startswith("http"):
                    website = "https://" + website

                if _skip_domain(website):
                    continue

                company = _TITLE_STRIP_RE.sub("", title).strip()
                if not company:
                    continue
                company_key = company.lower()[:50]
                if company_key in seen_companies:
                    continue

                phone = ""
                raw_phones = PHONE_RE.findall(snippet)
                for rp in raw_phones:
                    p = _clean_phone(rp)
                    if p and re.match(r"[6-9]\d{9}$", p) and p not in seen_phones:
                        phone = p
                        break

                if not website:
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
                    "source": "DuckDuckGo",
                })

            except Exception:
                continue

        print(f"  [DuckDuckGo] {len(leads)} results — {keyword} in {city}")
        time.sleep(1)

    except Exception as e:
        print(f"  [DuckDuckGo] Error: {e}")

    return leads
