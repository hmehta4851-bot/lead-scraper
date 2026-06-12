"""
DuckDuckGo HTML search scraper — 100% free, no API key, no rate limits.
Finds company websites via organic web search.
Phone-less results are passed to enricher.py to resolve contact details.
"""
import re
import time
from urllib.parse import urlparse
from scrapers.browser import get_page

PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9](?:[\-\s]?\d){9}")

# Skip these aggregate directories — we already scrape them directly
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
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

    page = get_page()
    try:
        page.goto(url, timeout=25000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        results = page.query_selector_all(".result__body, .result")

        for result in results:
            if len(leads) >= max_results:
                break
            try:
                title_el = result.query_selector(".result__a")
                snippet_el = result.query_selector(".result__snippet")
                url_el = result.query_selector(".result__url")

                title = (title_el.inner_text() if title_el else "").strip()
                snippet = (snippet_el.inner_text() if snippet_el else "").strip()
                result_url = (url_el.inner_text() if url_el else "").strip()

                if not title or len(title) < 5:
                    continue
                if _skip_domain(result_url):
                    continue

                # Clean company name from page title
                company = _TITLE_STRIP_RE.sub("", title).strip()
                if not company:
                    continue
                company_key = company.lower()[:50]
                if company_key in seen_companies:
                    continue

                # Normalise website URL
                website = result_url.strip()
                if website and not website.startswith("http"):
                    website = "https://" + website

                # Phone from snippet (bonus — enricher fills it later if missing)
                phone = ""
                raw_phones = PHONE_RE.findall(snippet)
                for rp in raw_phones:
                    p = _clean_phone(rp)
                    if p and re.match(r"[6-9]\d{9}$", p) and p not in seen_phones:
                        phone = p
                        break

                # Must have at least a website (enricher will fetch phone + email)
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
