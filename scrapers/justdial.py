"""
JustDial scraper — currently blocked (timeout / HTTP2 errors).
Returns empty list. Source replaced by Google Maps + Sulekha.
"""


def search(keyword: str, city: str, max_results: int = 30) -> list:
    print(f"  [JustDial] Skipped (blocked) — using Google Maps + Sulekha instead")
    return []
