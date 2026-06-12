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
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.sulekha.com/",
}

PHONE_RE = re.compile(r"[6-9]\d{9}")


def search(keyword, city, max_results=60):
    leads = []
    city_slug = city.lower().replace(" ", "-")
    kw_slug = keyword.lower().replace(" ", "-")
    url = f"https://www.sulekha.com/{kw_slug}/{city_slug}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return leads
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return leads

    cards = soup.select(".businesscard, .spListing, [class*='business-card'], [class*='sp-list']")
    if not cards:
        cards = soup.select("div[id^='splist'], li[class*='listing']")

    for card in cards[:max_results]:
        try:
            company = ""
            contact_person = ""
            phone = ""
            website = ""
            designation = "Owner"

            comp_el = card.select_one("h2, h3, .bname, [class*='business-name']")
            if comp_el:
                company = comp_el.get_text(strip=True)

            contact_el = card.select_one(".cname, .contactname, [class*='contact']")
            if contact_el:
                contact_person = contact_el.get_text(strip=True)

            phone_el = card.select_one(".phone, .tel, [class*='phone']")
            if phone_el:
                raw = phone_el.get_text(strip=True)
                match = PHONE_RE.search(re.sub(r"\D", "", raw))
                if match:
                    phone = match.group()

            if not phone:
                match = PHONE_RE.search(card.get_text())
                if match:
                    phone = match.group()

            web_el = card.select_one("a[href*='http']:not([href*='sulekha'])")
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
                "source": "Sulekha",
            })

        except Exception:
            continue

        time.sleep(0.4)

    return leads
