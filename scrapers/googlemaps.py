"""
Google Maps scraper — primary lead source.
Uses Playwright to search Google Maps for businesses matching keyword + city.
Returns company name, phone, website. Email/contact filled by enricher.
"""
import re
from scrapers.browser import get_page

PHONE_DIGITS_RE = re.compile(r"\d")


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def search(keyword: str, city: str, max_results: int = 40) -> list:
    leads = []
    query = f"{keyword} {city} india"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    page = get_page("Google Maps")
    try:
        loaded = False
        last_error = None
        for attempt in range(2):
            try:
                page.goto(url, timeout=45000, wait_until="commit")
                page.wait_for_timeout(5000 + (attempt * 2000))
                if page.query_selector('div[role="feed"], div[role="article"]'):
                    loaded = True
                    break
            except Exception as error:
                last_error = error

        if not loaded:
            if last_error:
                print(f"  [GoogleMaps] Navigation failed after retry: {last_error}")
            return leads

        # Scroll the results panel to load more listings
        try:
            panel = page.query_selector('div[role="feed"]')
            if panel:
                for _ in range(6):
                    panel.evaluate("el => el.scrollBy(0, 800)")
                    page.wait_for_timeout(1200)
        except Exception:
            pass

        articles = page.query_selector_all('div[role="article"]')
        seen_phones = set()

        for art in articles[:max_results]:
            try:
                text = art.inner_text()
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                if not lines:
                    continue

                # Google exposes the canonical listing name as the article label.
                # This avoids treating sponsored-card menu icons as company names.
                company = (art.get_attribute("aria-label") or "").strip()
                if not company:
                    name_link = art.query_selector("a.hfpxzc[aria-label]")
                    if name_link:
                        company = (name_link.get_attribute("aria-label") or "").strip()
                if not company:
                    name_el = art.query_selector("div.fontHeadlineSmall, div.qBF1Pd")
                    if name_el:
                        company = name_el.inner_text().strip()
                if not company:
                    continue

                # Extract phone — Google formats as "XXXXX XXXXX"
                phone = ""
                for ln in lines:
                    raw_digits = re.sub(r"\D", "", ln)
                    if len(raw_digits) >= 10:
                        candidate = _clean_phone(ln)
                        if candidate and re.match(r"[6-9]\d{9}", candidate):
                            phone = candidate
                            break

                # Extract website link
                website = ""
                links = art.query_selector_all("a[href]")
                for lnk in links:
                    href = lnk.get_attribute("href") or ""
                    if href.startswith("http") and "google" not in href and "maps" not in href:
                        website = href.split("?")[0]
                        break

                if not phone and not website:
                    continue

                if phone and phone in seen_phones:
                    continue
                if phone:
                    seen_phones.add(phone)

                leads.append(
                    {
                        "company": company,
                        "contact_person": "",
                        "phone": phone,
                        "email": "",
                        "designation": "",
                        "website": website,
                        "source": "Google Maps",
                    }
                )

            except Exception:
                continue

    except Exception as e:
        print(f"  [GoogleMaps] Error: {e}")

    return leads
