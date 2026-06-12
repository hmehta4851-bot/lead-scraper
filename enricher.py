import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}")

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus", "/contact_us",
    "/about", "/about-us", "/reach-us", "/get-in-touch",
]


def _get(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def _extract_emails(text):
    found = EMAIL_RE.findall(text or "")
    cleaned = [
        e for e in found
        if not any(skip in e.lower() for skip in [
            "example", "domain", "email", "test", "noreply", "no-reply",
            ".png", ".jpg", ".gif", "sentry", "wixpress", "shopify"
        ])
    ]
    return list(dict.fromkeys(cleaned))


def _extract_phones(text):
    found = PHONE_RE.findall(text or "")
    cleaned = [re.sub(r"[\s\-]", "", p.replace("+91", "")) for p in found]
    cleaned = [p[-10:] for p in cleaned if len(p) >= 10]
    return list(dict.fromkeys(cleaned))


def _extract_name_from_page(soup):
    for tag in ["h1", "h2", "h3"]:
        els = soup.find_all(tag)
        for el in els:
            text = el.get_text(strip=True)
            words = text.split()
            if 2 <= len(words) <= 4 and text[0].isupper():
                return text
    return None


def enrich_website(url):
    """Returns dict with email, phone, contact_person, designation (all may be empty)."""
    result = {"email": "", "phone": "", "contact_person": "", "designation": ""}

    if not url or not url.startswith("http"):
        return result

    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    pages_to_check = [url]

    for path in CONTACT_PATHS:
        pages_to_check.append(urljoin(base, path))

    all_emails = []
    all_phones = []

    for page_url in pages_to_check[:5]:
        html = _get(page_url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        emails = _extract_emails(text)
        phones = _extract_phones(text)

        all_emails.extend(emails)
        all_phones.extend(phones)

        if emails or phones:
            if not result["contact_person"]:
                name = _extract_name_from_page(soup)
                if name:
                    result["contact_person"] = name

        time.sleep(0.5)

        if all_emails and all_phones:
            break

    if all_emails:
        result["email"] = all_emails[0]
    if all_phones:
        result["phone"] = all_phones[0]

    return result
