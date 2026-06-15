"""
Bing HTML search scraper — free, no API key.
Different crawl index than DuckDuckGo — surfaces different businesses.
Phone-less leads enriched later by enricher.py.
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
    "reddit", "bing", "microsoft", "yellowpages",
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


def _rss_results(xml_text: str, max_results: int) -> list[dict]:
    leads = []
    seen_companies = set()
    soup = BeautifulSoup(xml_text, "xml")
    for item in soup.select("item"):
        if len(leads) >= max_results:
            break
        title_node = item.find("title")
        link_node = item.find("link")
        description_node = item.find("description")
        title = title_node.get_text(" ", strip=True) if title_node else ""
        website = link_node.get_text(" ", strip=True) if link_node else ""
        snippet = (
            description_node.get_text(" ", strip=True)
            if description_node
            else ""
        )
        if len(title) < 5 or not website.startswith("http"):
            continue
        if _skip_domain(website):
            continue
        company = _TITLE_STRIP_RE.sub("", title).strip()
        company_key = company.casefold()[:80]
        if len(company) < 3 or company_key in seen_companies:
            continue
        phone = ""
        for raw in PHONE_RE.findall(snippet):
            candidate = _clean_phone(raw)
            if re.fullmatch(r"[6-9]\d{9}", candidate):
                phone = candidate
                break
        seen_companies.add(company_key)
        leads.append(
            {
                "company": company,
                "contact_person": "",
                "phone": phone,
                "email": "",
                "designation": "",
                "website": website,
                "website_text": f"{title} {snippet}",
                "source": "Bing",
            }
        )
    return leads


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
    url = f"https://www.bing.com/search?q={quote_plus(query)}&count=20"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  [Bing] HTTP {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.select("li.b_algo")

        for result in results:
            if len(leads) >= max_results:
                break
            try:
                title_el = result.select_one("h2 a")
                snippet_el = result.select_one(".b_caption p, .b_paractl")
                cite_el = result.select_one("cite")

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                cite_text = cite_el.get_text(strip=True) if cite_el else ""

                if not title or len(title) < 5:
                    continue

                href = title_el.get("href", "")
                website = href if href.startswith("http") else ""
                if not website and cite_text:
                    website = cite_text if cite_text.startswith("http") else f"https://{cite_text}"

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
                    "website_text": f"{title} {snippet}",
                    "source": "Bing",
                })

            except Exception:
                continue

        if not leads:
            rss_url = (
                f"https://www.bing.com/search?"
                f"q={quote_plus(query)}&format=rss"
            )
            rss_response = requests.get(
                rss_url,
                headers=HEADERS,
                timeout=15,
                allow_redirects=True,
            )
            if rss_response.status_code == 200:
                leads = _rss_results(rss_response.text, max_results)
                if leads:
                    print(
                        f"  [Bing] HTML empty; RSS fallback produced "
                        f"{len(leads)} results"
                    )
            else:
                print(f"  [Bing RSS] HTTP {rss_response.status_code}")

        print(f"  [Bing] {len(leads)} results — {keyword} in {city}")
        time.sleep(1)

    except Exception as e:
        print(f"  [Bing] Error: {e}")

    return leads
