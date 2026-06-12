import re
import time
import requests
from bs4 import BeautifulSoup
from enricher import enrich_website

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/90.0.4430.212 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "en-IN,en;q=0.9",
}

PHONE_RE = re.compile(r"[6-9]\d{9}")

JD_DIGIT_MAP = {
    "b": "0", "c": "1", "d": "2", "e": "3", "f": "4",
    "g": "5", "h": "6", "i": "7", "j": "8", "k": "9",
    "l": "0", "m": "1", "n": "2", "o": "3", "p": "4",
    "q": "5", "r": "6", "s": "7", "t": "8", "u": "9",
}


def _decode_jd_phone(encoded):
    result = ""
    for ch in encoded.lower():
        if ch in JD_DIGIT_MAP:
            result += JD_DIGIT_MAP[ch]
        elif ch.isdigit():
            result += ch
    digits = re.sub(r"\D", "", result)
    return digits[-10:] if len(digits) >= 10 else ""


def _extract_phone_from_card(card):
    phone_span = card.select_one(".contact-info .tel, .jdphone, [class*='mobilesv']")
    if phone_span:
        raw = phone_span.get("data-jdphone") or phone_span.get_text(strip=True)
        if raw:
            decoded = _decode_jd_phone(raw)
            if decoded:
                return decoded

    all_spans = card.select("span[class]")
    collected = ""
    for span in all_spans:
        cls = " ".join(span.get("class", []))
        if any(c in cls for c in ["mobilesv", "jdphone", "telno"]):
            collected += span.get_text(strip=True)

    if collected:
        decoded = _decode_jd_phone(collected)
        if decoded:
            return decoded

    text = card.get_text()
    match = PHONE_RE.search(text)
    if match:
        return match.group()

    return ""


def search(keyword, city, max_results=60):
    leads = []
    city_slug = city.lower().replace(" ", "-")
    keyword_slug = keyword.lower().replace(" ", "-")
    url = f"https://www.justdial.com/{city_slug}/{keyword_slug}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code not in (200, 206):
            return leads
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return leads

    cards = soup.select(".resultbox_info, .cntanr, [class*='resultbox']")
    if not cards:
        cards = soup.select("li.cntanr, div[class*='store-card']")

    for card in cards[:max_results]:
        try:
            company = ""
            contact_person = ""
            phone = ""
            website = ""
            designation = "Owner"

            comp_el = card.select_one(".resultbox_title_anchor, .jdtitle, h2 a, h3 a")
            if comp_el:
                company = comp_el.get_text(strip=True)

            phone = _extract_phone_from_card(card)

            web_el = card.select_one("a[href*='http']:not([href*='justdial'])")
            if web_el:
                website = web_el.get("href", "")

            if not company:
                continue

            email = ""
            if website:
                enriched = enrich_website(website)
                email = enriched.get("email", "")
                if not phone:
                    phone = enriched.get("phone", "")
                if not contact_person:
                    contact_person = enriched.get("contact_person", "")

            leads.append({
                "company": company,
                "contact_person": contact_person,
                "phone": phone,
                "email": email,
                "designation": designation,
                "website": website,
                "source": "JustDial",
            })

        except Exception:
            continue

        time.sleep(0.4)

    return leads
