import re
import time
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9](?:[\-\s]?\d){9}")
WA_RE = re.compile(
    r"wa\.me/\+?91([6-9]\d{9})"
    r"|wa\.me/([6-9]\d{9})"
    r"|api\.whatsapp\.com/send\?phone=91([6-9]\d{9})"
    r"|api\.whatsapp\.com/send\?phone=([6-9]\d{9})"
)

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus", "/contact_us",
    "/about", "/about-us", "/reach-us", "/get-in-touch",
    "/team", "/our-team", "/management", "/leadership", "/about-us/team",
]

DESIGNATIONS = (
    "Managing Director", "Director", "Proprietor", "Co-Founder", "Founder",
    "Business Owner", "Owner", "Chief Executive Officer", "CEO", "Partner",
    "General Manager", "Manager", "Chairman", "President",
)

GENERIC_NAME_WORDS = {
    "about", "about us", "contact", "contact us", "get in touch", "reach us",
    "our team", "meet the team", "leadership", "management", "welcome",
    "home", "services", "products", "portfolio", "gallery", "testimonials",
    "blog", "careers", "privacy policy", "terms", "perfect", "surface",
    "every", "game", "quality", "sports", "solutions", "company", "flooring",
}

NAME_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z.'-]*$")


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


def _clean_candidate(value):
    value = re.sub(r"\s+", " ", value or "").strip(" \t\r\n,;:|-/")
    value = re.sub(r"^(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+", "", value, flags=re.I)
    return value


def _is_person_name(value):
    value = _clean_candidate(value)
    words = value.split()
    if not 2 <= len(words) <= 4 or len(value) > 60:
        return False
    if value.lower() in GENERIC_NAME_WORDS:
        return False
    if any(word.lower() in GENERIC_NAME_WORDS for word in words):
        return False
    if any(not NAME_TOKEN_RE.match(word) for word in words):
        return False
    if any(word.lower() in {"pvt", "ltd", "limited", "llp", "inc", "india"} for word in words):
        return False
    return all(word[0].isupper() for word in words)


def _extract_jsonld_people(soup):
    people = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text() or "{}")
        except (TypeError, ValueError):
            continue

        stack = data if isinstance(data, list) else [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
                continue
            if not isinstance(item, dict):
                continue
            stack.extend(v for v in item.values() if isinstance(v, (dict, list)))
            if str(item.get("@type", "")).lower() != "person":
                continue
            name = _clean_candidate(str(item.get("name", "")))
            if _is_person_name(name):
                people.append((name, str(item.get("jobTitle", "")).strip()))
    return people


def _extract_contact_from_page(soup):
    people = _extract_jsonld_people(soup)
    if people:
        return people[0]

    text = soup.get_text(" ", strip=True)
    designation_pattern = "|".join(re.escape(value) for value in DESIGNATIONS)
    patterns = [
        re.compile(
            rf"\b(?P<designation>{designation_pattern})\b\s*[:\-–—,]?\s*"
            r"(?P<name>(?:(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+)?"
            r"[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3})",
            re.I,
        ),
        re.compile(
            r"\b(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+"
            r"(?P<name>[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3})"
            rf"(?:\s*[,|\-–—]\s*(?P<designation>{designation_pattern}))?",
            re.I,
        ),
        re.compile(
            r"\b(?P<name>[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3})"
            rf"\s*[,|\-–—]\s*(?P<designation>{designation_pattern})\b",
            re.I,
        ),
    ]

    for pattern in patterns:
        for match in pattern.finditer(text):
            name = _clean_candidate(match.group("name"))
            if not _is_person_name(name):
                continue
            designation = (match.groupdict().get("designation") or "").strip()
            return name, designation

    return "", ""


def enrich_website(url, max_pages: int = 5):
    """Returns dict with email, phone, contact_person, designation (all may be empty)."""
    result = {
        "email": "",
        "phone": "",
        "contact_person": "",
        "designation": "",
        "website_text": "",
    }

    if not url or not url.startswith("http"):
        return result

    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    pages_to_check = [url]

    for path in CONTACT_PATHS:
        pages_to_check.append(urljoin(base, path))

    all_emails = []
    all_phones = []

    for page_url in pages_to_check[:max_pages]:
        html = _get(page_url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        if not result["website_text"]:
            result["website_text"] = text[:12000]

        # mailto: links are the most reliable email source — prioritize them
        for a in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
            raw_email = a.get("href", "")[7:].split("?")[0].strip().lower()
            cleaned = _extract_emails(raw_email)
            all_emails = cleaned + all_emails  # prepend = higher priority

        emails = _extract_emails(text)
        phones = _extract_phones(text)

        all_emails.extend(emails)
        all_phones.extend(phones)

        # WhatsApp links contain verified phone numbers (most reliable source)
        for a in soup.find_all("a", href=True):
            m = WA_RE.search(a["href"])
            if m:
                wa_phone = next((g for g in m.groups() if g), "")
                if wa_phone and re.match(r"[6-9]\d{9}$", wa_phone):
                    all_phones = [wa_phone] + all_phones  # prepend = higher priority

        if not result["contact_person"]:
            name, designation = _extract_contact_from_page(soup)
            if name:
                result["contact_person"] = name
                result["designation"] = designation

        time.sleep(0.5)

        if all_emails and all_phones:
            break

    if all_emails:
        result["email"] = all_emails[0]
    if all_phones:
        result["phone"] = all_phones[0]

    return result


# ── Parallel contact-name resolver ────────────────────────────────────────────

_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def _name_from_ddg(query: str):
    """Search DuckDuckGo HTML, extract first person name + designation from snippets."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        resp = requests.get(url, headers=_SEARCH_HEADERS, timeout=10, allow_redirects=True)
        if resp.status_code != 200:
            return "", ""
        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = soup.select(".result__snippet, .result__body")
        text = " ".join(s.get_text(" ", strip=True) for s in snippets[:6])
        if text:
            return _extract_contact_from_page(BeautifulSoup(f"<div>{text}</div>", "html.parser"))
    except Exception:
        pass
    return "", ""


def _resolve_one(lead: dict, city: str):
    """Try to find a contact person name for a single lead via web search."""
    company = lead.get("company", "").strip()
    phone = lead.get("phone", "").strip()
    if not company:
        return

    # Pass 1: phone number search — very specific, best signal
    if phone:
        name, desig = _name_from_ddg(f'"{phone}" owner director proprietor')
        if name:
            lead["contact_person"] = name
            if desig and not lead.get("designation"):
                lead["designation"] = desig
            return

    # Pass 2: company + city search
    name, desig = _name_from_ddg(
        f'"{company}" {city} owner director proprietor contact person'
    )
    if name:
        lead["contact_person"] = name
        if desig and not lead.get("designation"):
            lead["designation"] = desig


def resolve_contact_names(leads: list, city: str, max_workers: int = 6) -> list:
    """
    Parallel web-search fallback: fills contact_person for leads where
    website enrichment found nothing. Mutates leads in-place, returns same list.
    """
    targets = [l for l in leads if not l.get("contact_person") and l.get("company")]
    if not targets:
        return leads

    print(f"  [NameResolver] Searching names for {len(targets)} leads in parallel...")
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_resolve_one, lead, city): lead for lead in targets}
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception:
                pass

    filled = sum(1 for l in targets if l.get("contact_person"))
    print(f"  [NameResolver] Filled {filled}/{len(targets)} names")
    return leads
