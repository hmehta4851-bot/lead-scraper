"""
TradeIndia B2B directory scraper — free, no API key needed.
Indian B2B marketplace: suppliers, dealers, manufacturers.
Phone numbers hidden behind JS click — falls back to website-only leads
which get enriched later by enricher.py.
"""
import re
import time
from scrapers.browser import get_page

PHONE_RE = re.compile(r"[6-9]\d{9}")


def _clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else ""


def search(keyword: str, city: str, max_results: int = 20) -> list:
    leads = []
    seen_phones: set = set()
    seen_companies: set = set()

    query = keyword.replace(" ", "+")
    city_enc = city.replace(" ", "+")
    url = (
        f"https://www.tradeindia.com/search.html"
        f"?keyword={query}&cntry=india&city={city_enc}"
    )

    page = get_page()
    try:
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Try clicking "View Phone" / "Contact Supplier" buttons to reveal numbers
        view_btns = page.query_selector_all(
            "button[class*='view'], a[class*='phone'], "
            "[class*='viewphone'], [class*='view-phone'], "
            "[class*='contact-btn'], [class*='viewcontact']"
        )
        for btn in view_btns[:15]:
            try:
                btn.click(timeout=1500)
                page.wait_for_timeout(400)
            except Exception:
                pass

        # Company listing blocks — TradeIndia uses multiple layout variants
        blocks = page.query_selector_all(
            ".product-dtl-box, .product-list-item, .company-detail-box, "
            ".listing-item, .product-listing, .company-list-item, "
            "[class*='product-dtl'], [class*='listing-box']"
        )

        for block in blocks[:max_results + 5]:
            try:
                block_text = block.inner_text()

                # Company name
                name_el = block.query_selector(
                    "h2, h3, h4, "
                    "[class*='company-name'], [class*='firm-name'], "
                    "[class*='company_name'], [class*='companyname']"
                )
                company = (name_el.inner_text() if name_el else "").strip()
                # Fallback: first non-empty line of block
                if not company:
                    for line in block_text.splitlines():
                        line = line.strip()
                        if len(line) > 4:
                            company = line
                            break
                if not company or len(company) < 3:
                    continue

                company_key = company.lower()[:50]
                if company_key in seen_companies:
                    continue

                # Phone — scan block text
                raw_phones = PHONE_RE.findall(re.sub(r"[\s\-]", "", block_text))
                phone = ""
                for rp in raw_phones:
                    p = _clean_phone(rp)
                    if p and re.match(r"[6-9]\d{9}$", p) and p not in seen_phones:
                        phone = p
                        break

                # External website link (not tradeindia.com)
                link_el = block.query_selector(
                    "a[href^='http']:not([href*='tradeindia'])"
                )
                website = (
                    link_el.get_attribute("href") if link_el else ""
                ).strip()

                # Need phone OR website to be useful
                if not phone and not website:
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
                    "source": "TradeIndia",
                })

                if len(leads) >= max_results:
                    break

            except Exception:
                continue

        print(f"  [TradeIndia] {len(leads)} leads — {keyword} in {city}")
        time.sleep(1)

    except Exception as e:
        print(f"  [TradeIndia] Error: {e}")

    return leads
