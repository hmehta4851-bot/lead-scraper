"""OpenStreetMap buyer-directory scraper using free public OSM endpoints."""

from __future__ import annotations

import re
import time
from functools import lru_cache

import requests


HEADERS = {
    "User-Agent": "SunzoneLeadResearch/1.0 (contact: sales@sunzone.in)",
    "Accept-Language": "en",
}
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)


def _clean_phone(raw: str) -> str:
    for value in re.split(r"[,;/]", str(raw)):
        digits = re.sub(r"\D", "", value)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        if digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]
        if re.fullmatch(r"[6-9]\d{9}", digits):
            return digits
    return ""


@lru_cache(maxsize=64)
def _city_coordinates(city: str) -> tuple[float, float] | None:
    response = requests.get(
        NOMINATIM_URL,
        params={"q": f"{city}, India", "format": "jsonv2", "limit": 1},
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    results = response.json()
    time.sleep(1.05)
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


def _tag_filters(keyword: str) -> list[tuple[str, str]]:
    text = keyword.casefold()
    filters: list[tuple[str, str]] = []
    rules = (
        (("gym", "fitness", "crossfit", "health club"), ("leisure", "fitness_centre")),
        (("sports academy", "football academy", "cricket academy", "hockey academy",
          "tennis academy", "badminton academy", "basketball academy",
          "athletics academy"), ("leisure", "sports_centre")),
        (("preschool", "play school", "nursery", "kindergarten", "daycare"), ("amenity", "kindergarten")),
        (("school",), ("amenity", "school")),
        (("college",), ("amenity", "college")),
        (("university",), ("amenity", "university")),
        (("stadium",), ("leisure", "stadium")),
        (("sports complex", "sports club", "badminton club", "padel club"), ("leisure", "sports_centre")),
        (("hotel",), ("tourism", "hotel")),
        (("resort",), ("tourism", "resort")),
        (("hospital", "physiotherapy", "rehabilitation"), ("amenity", "hospital")),
        (("park",), ("leisure", "park")),
        (("mall",), ("shop", "mall")),
    )
    for needles, tag_filter in rules:
        if any(needle in text for needle in needles):
            filters.append(tag_filter)
    return filters[:2] or [("leisure", "sports_centre")]


def _overpass_query(lat: float, lon: float, filters: list[tuple[str, str]]) -> str:
    selectors = []
    for key, value in filters:
        selectors.extend(
            (
                f'node["{key}"="{value}"](around:30000,{lat},{lon});',
                f'way["{key}"="{value}"](around:30000,{lat},{lon});',
                f'relation["{key}"="{value}"](around:30000,{lat},{lon});',
            )
        )
    return "[out:json][timeout:35];(" + "".join(selectors) + ");out center tags;"


@lru_cache(maxsize=128)
def _fetch_elements(
    city: str,
    filters: tuple[tuple[str, str], ...],
) -> tuple[dict, ...]:
    coordinates = _city_coordinates(city)
    if not coordinates:
        return ()
    query = _overpass_query(*coordinates, list(filters))
    last_error: Exception | None = None
    for endpoint in OVERPASS_URLS:
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                headers=HEADERS,
                timeout=45,
            )
            response.raise_for_status()
            return tuple(response.json().get("elements", []))
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error
    return ()


def search(keyword: str, city: str, max_results: int = 15) -> list[dict]:
    leads: list[dict] = []
    seen: set[str] = set()
    try:
        filters = tuple(_tag_filters(keyword))
        for element in _fetch_elements(city, filters):
            if len(leads) >= max_results:
                break
            tags = element.get("tags", {})
            company = str(tags.get("name", "")).strip()
            if len(company) < 3 or company.casefold() in seen:
                continue
            phone = _clean_phone(tags.get("contact:phone") or tags.get("phone") or "")
            website = str(
                tags.get("contact:website") or tags.get("website") or ""
            ).strip()
            if website and not website.startswith("http"):
                website = f"https://{website}"
            if not phone and not website:
                continue
            email = str(tags.get("contact:email") or tags.get("email") or "").strip()
            context = " ".join(
                str(value)
                for key, value in tags.items()
                if key in {
                    "name", "description", "amenity", "leisure", "sport",
                    "tourism", "shop", "operator", "brand",
                }
            )
            seen.add(company.casefold())
            leads.append(
                {
                    "company": company,
                    "contact_person": "",
                    "phone": phone,
                    "email": email,
                    "designation": "",
                    "website": website,
                    "website_text": context,
                    "source": "OpenStreetMap",
                }
            )
    except Exception as exc:
        print(f"  [OpenStreetMap] Error: {exc}")
        raise

    print(f"  [OpenStreetMap] {len(leads)} results — {keyword} in {city}")
    return leads
