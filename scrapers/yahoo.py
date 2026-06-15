"""Yahoo web-search scraper. Free HTML results, no account or API key."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup


PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9](?:[\-\s]?\d){9}")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}
SKIP_DOMAINS = {
    "yahoo", "google", "facebook", "youtube", "wikipedia", "amazon",
    "flipkart", "indiamart", "tradeindia", "sulekha", "justdial",
    "exportersindia", "linkedin", "instagram", "quora", "reddit",
}
TITLE_STRIP_RE = re.compile(
    r"\s*[|\-–—]\s*.+$"
    r"|\s*(Pvt\.?|Ltd\.?|Private\s+Limited|Official\s+(Website|Site))\s*$",
    re.I,
)


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def _result_url(href: str) -> str:
    if "r.search.yahoo.com" in href:
        match = re.search(r"/RU=([^/]+)", href)
        if match:
            return unquote(match.group(1))
        parsed = parse_qs(urlparse(href).query)
        return parsed.get("RU", [""])[0]
    return href


def _skip(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return not host or any(domain in host for domain in SKIP_DOMAINS)


def search(keyword: str, city: str, max_results: int = 15) -> list[dict]:
    query = quote_plus(f"{keyword} {city} India phone contact")
    url = f"https://search.yahoo.com/search?p={query}&n=20"
    leads: list[dict] = []
    seen: set[str] = set()

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"  [Yahoo] HTTP {response.status_code}")
            raise RuntimeError(f"Yahoo HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        for result in soup.select("div.algo, div.dd.algo"):
            if len(leads) >= max_results:
                break
            link = result.select_one(".compTitle > a[href], a[data-matarget='algo']")
            if not link:
                continue
            website = _result_url(link.get("href", "")).strip()
            if not website.startswith("http") or _skip(website):
                continue
            title_node = link.select_one("h3") or result.select_one("h3")
            title = (
                title_node.get_text(" ", strip=True)
                if title_node
                else link.get_text(" ", strip=True)
            )
            company = TITLE_STRIP_RE.sub("", title).strip()
            key = company.casefold()[:80]
            if len(company) < 3 or key in seen:
                continue

            snippet_node = result.select_one(".compText, .fc-falcon")
            snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
            phone = ""
            for raw in PHONE_RE.findall(snippet):
                candidate = _clean_phone(raw)
                if re.fullmatch(r"[6-9]\d{9}", candidate):
                    phone = candidate
                    break

            seen.add(key)
            leads.append(
                {
                    "company": company,
                    "contact_person": "",
                    "phone": phone,
                    "email": "",
                    "designation": "",
                    "website": website,
                    "website_text": f"{title} {snippet}",
                    "source": "Yahoo",
                }
            )
    except Exception as exc:
        print(f"  [Yahoo] Error: {exc}")
        raise

    print(f"  [Yahoo] {len(leads)} results — {keyword} in {city}")
    return leads
