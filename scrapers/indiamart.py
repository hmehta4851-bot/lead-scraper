import re
import time
import requests
from bs4 import BeautifulSoup
from enricher import enrich_website

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://dir.indiamart.com/",
}

PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}")

DESIGNATION_KEYWORDS = [
    "Proprietor", "Director", "CEO", "MD", "Manager", "Owner",
    "Partner", "Founder", "Chairman", "President", "Head",
]


def _clean_phone(p):
    p = re.sub(r"[\s\-\(\)]", "", p)
    p = p.replace("+91", "")
    return p[-10:] if len(p) >= 10 else ""


def _get_glid_phone(glid):
    try:
        url = f"https://dir.indiamart.com/api/contactdetails.php?glid={glid}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            mobile = data.get("mobileNumber") or data.get("mobile") or ""
            phone = data.get("phone") or ""
            return _clean_phone(str(mobile or phone))
    except Exception:
        pass
    return ""


def _find_designation(text):
    for kw in DESIGNATION_KEYWORDS:
        if kw.lower() in text.lower():
            return kw
    return ""


def search(keyword, city, max_results=60):
    leads = []
    query = f"{keyword} {city}"
    url = f"https://dir.indiamart.com/search.mp?ss={requests.utils.quote(query)}&prdsrc=1"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return leads
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return leads

    cards = soup.select(".productscard, .unitCard, .bsrUnitCard, .product-unit")
    if not cards:
        cards = soup.select("[id^='PRDCAT'], [class*='unit']")

    for card in cards[:max_results]:
        try:
            company = ""
            contact_person = ""
            phone = ""
            website = ""
            designation = ""

            comp_el = card.select_one(".companyname, .company-name, .lcname, [class*='company']")
            if comp_el:
                company = comp_el.get_text(strip=True)

            contact_el = card.select_one(".contactname, .contact-name, [class*='contact']")
            if contact_el:
                contact_text = contact_el.get_text(strip=True)
                parts = contact_text.split("-")
                if len(parts) >= 2:
                    contact_person = parts[0].strip()
                    designation = parts[1].strip()
                else:
                    contact_person = contact_text

            if not designation:
                full_text = card.get_text(" ", strip=True)
                designation = _find_designation(full_text)

            glid_match = re.search(r"glid[=:](\d+)", str(card))
            if glid_match:
                glid = glid_match.group(1)
                phone = _get_glid_phone(glid)
                time.sleep(0.3)

            if not phone:
                phone_match = PHONE_RE.search(card.get_text())
                if phone_match:
                    phone = _clean_phone(phone_match.group())

            web_el = card.select_one("a[href*='http']:not([href*='indiamart'])")
            if web_el:
                website = web_el.get("href", "")

            if company and not phone and not website:
                continue

            if not all([company, contact_person, phone, designation]):
                if website:
                    enriched = enrich_website(website)
                    if not phone:
                        phone = enriched.get("phone", "")
                    if not contact_person:
                        contact_person = enriched.get("contact_person", "")
                    if not designation:
                        designation = "Owner"

            lead = {
                "company": company,
                "contact_person": contact_person,
                "phone": phone,
                "email": "",
                "designation": designation,
                "website": website,
                "source": "IndiaMART",
            }

            if website:
                enriched = enrich_website(website)
                if not lead["email"]:
                    lead["email"] = enriched.get("email", "")
                if not lead["phone"]:
                    lead["phone"] = enriched.get("phone", "")
                if not lead["contact_person"]:
                    lead["contact_person"] = enriched.get("contact_person", "")

            leads.append(lead)

        except Exception:
            continue

        time.sleep(0.5)

    return leads
