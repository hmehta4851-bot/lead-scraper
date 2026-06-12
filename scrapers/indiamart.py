"""
IndiaMART scraper — currently blocked by bot detection / login wall.
Returns empty list. Source replaced by Google Maps + Sulekha.
"""


def search(keyword: str, city: str, max_results: int = 30) -> list:
    print(f"  [IndiaMART] Skipped (login wall) — using Google Maps + Sulekha instead")
    return []
