"""Quick live smoke test with no Google Sheets or credentials."""
import sys

sys.path.insert(0, "/Users/admin/lead-scraper")

from scrapers import browser, googlemaps, sulekha

KEYWORD = "sports flooring contractor"
CITY = "Mumbai"


def print_lead(i, lead, source):
    print(f"\n  Lead #{i+1} [{source}]")
    print(f"    Company    : {lead.get('company', '')}")
    print(f"    Contact    : {lead.get('contact_person', '')} ({lead.get('designation', '')})")
    print(f"    Phone      : {lead.get('phone', '')}")
    print(f"    Email      : {lead.get('email', '')}")
    print(f"    Website    : {lead.get('website', '')}")


def main():
    print(f"\n{'='*60}")
    print(f"  LEAD SCRAPER TEST RUN")
    print(f"  Keyword : {KEYWORD}")
    print(f"  City    : {CITY}")
    print(f"{'='*60}")
    print("\n[1/2] Searching Google Maps...")
    maps_leads = googlemaps.search(KEYWORD, CITY, max_results=5)
    print(f"  Results: {len(maps_leads)}")
    if not maps_leads:
        raise RuntimeError("Google Maps returned no leads after its navigation retry")
    for i, lead in enumerate(maps_leads[:3]):
        print_lead(i, lead, "Google Maps")
    if any(not lead.get("company") or lead["company"] in {"", "Sponsored"} for lead in maps_leads):
        raise RuntimeError("Google Maps returned an invalid company name")
    if any(
        lead.get("contact_person", "").strip().lower()
        in {"about us", "quality sports", "perfect surface for every game"}
        for lead in maps_leads
    ):
        raise RuntimeError("Website enrichment returned a heading instead of a person")

    print("\n[2/2] Searching Sulekha...")
    sulekha_leads = sulekha.search(KEYWORD, CITY, max_results=5)
    print(f"  Results: {len(sulekha_leads)}")
    for i, lead in enumerate(sulekha_leads[:3]):
        print_lead(i, lead, "Sulekha")

    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"  Google Maps : {len(maps_leads)}")
    print(f"  Sulekha     : {len(sulekha_leads)}")
    print(f"  Total       : {len(maps_leads) + len(sulekha_leads)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    finally:
        browser.close()
