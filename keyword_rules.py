"""Product-level keyword integrity rules for Sunzone Prospect Flow."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordRule:
    required_any: tuple[str, ...]
    excluded_any: tuple[str, ...] = ()


def _terms(*values: str) -> tuple[str, ...]:
    return tuple(value.casefold() for value in values)


PRODUCT_KEYWORD_RULES: dict[tuple[str, str], KeywordRule] = {
    ("Playful", "EPDM Playground / Wet Pour Flooring"): KeywordRule(
        required_any=_terms(
            "epdm flooring", "epdm system", "wet pour", "wetpour",
            "playground flooring", "play area flooring",
            "children flooring", "kids flooring", "rubber flooring",
        ),
        excluded_any=_terms(
            "granule", "pu binder", "rubber roll", "gym rubber",
            "running track", "athletic track",
        ),
    ),
    ("Playful", "EPDM Granules / SBR Granules / PU Binder"): KeywordRule(
        required_any=_terms(
            "epdm granule", "sbr granule", "rubber granule",
            "pu binder", "polyurethane binder",
        ),
        excluded_any=_terms(
            "epdm flooring", "wet pour flooring", "playground flooring",
            "running track", "athletic track",
        ),
    ),
    ("Graceful", "Football Turf / Box Cricket Turnkey"): KeywordRule(
        required_any=_terms(
            "football turf", "football ground", "football field",
            "football pitch", "futsal turf", "box cricket",
        ),
        excluded_any=_terms(
            "cricket pitch turf", "cricket wicket", "hockey turf",
            "tennis turf", "padel turf",
        ),
    ),
    ("Graceful", "Artificial Cricket Pitch / Cricket Turf"): KeywordRule(
        required_any=_terms(
            "cricket pitch", "cricket turf", "cricket wicket",
            "practice wicket",
        ),
        excluded_any=_terms("box cricket", "football turf", "hockey turf"),
    ),
    ("Graceful", "Artificial Grass / Landscape Turf"): KeywordRule(
        required_any=_terms(
            "artificial grass", "artifical grass", "synthetic grass",
            "landscape turf", "landscaping turf", "garden turf",
            "balcony grass", "lawn grass",
        ),
        excluded_any=_terms(
            "football", "cricket", "hockey", "tennis", "padel",
            "gym turf", "sled track",
        ),
    ),
    ("Graceful", "FIH Hockey Turf"): KeywordRule(
        required_any=_terms("hockey turf", "hockey field", "hockey pitch"),
        excluded_any=_terms("football", "cricket", "tennis", "padel"),
    ),
    ("Graceful", "Multi-Sport Turf / Tennis Turf / Padel Turf"): KeywordRule(
        required_any=_terms(
            "multi sport turf", "multisport turf", "multi-sport turf",
            "tennis turf", "padel turf", "padel grass",
        ),
        excluded_any=_terms(
            "football turf", "cricket turf", "hockey turf", "gym turf",
        ),
    ),
    ("Graceful", "Turf Accessories"): KeywordRule(
        required_any=_terms(
            "turf adhesive", "grass adhesive", "turf glue", "grass glue",
            "joining tape", "seaming tape", "jointing tape", "shock pad",
            "turf infill", "silica sand", "rubber infill",
            "turf nail", "turf accessory", "turf accessories",
        ),
        excluded_any=_terms(
            "gym mat", "rubber tile", "court tile", "badminton flooring",
        ),
    ),
    ("Powerful", "Gym Astro Turf / Sled Track Turf"): KeywordRule(
        required_any=_terms(
            "gym turf", "gym astro turf", "gym astroturf",
            "sled turf", "sled track", "functional turf",
            "fitness turf", "crossfit turf",
        ),
        excluded_any=_terms(
            "football", "cricket", "hockey", "tennis", "padel",
            "landscape", "garden",
        ),
    ),
    ("Powerful", "Gym PVC Sports Flooring"): KeywordRule(
        required_any=_terms(
            "gym pvc", "gym vinyl", "fitness pvc", "fitness vinyl",
            "aerobic flooring", "aerobics flooring",
        ),
        excluded_any=_terms(
            "badminton", "wooden", "rubber roll", "rubber tile",
        ),
    ),
    ("Powerful", "Gym Rubber Roll Flooring"): KeywordRule(
        required_any=_terms(
            "rubber roll", "rolled rubber", "gym roll",
            "gym rubber flooring roll",
        ),
        excluded_any=_terms(
            "playground", "running track", "athletic track",
            "rubber tile", "rubber mat",
        ),
    ),
    ("Powerful", "Gym Rubber Tiles / Laminate Tiles / Mats"): KeywordRule(
        required_any=_terms(
            "gym rubber tile", "gym tile", "gym flooring tile",
            "gym mat", "gym flooring mat", "rubber gym mat",
            "laminate gym tile",
        ),
        excluded_any=_terms(
            "playground", "children", "kids", "badminton court tile",
            "sports court tile", "rubber roll",
        ),
    ),
    ("Joyful", "PVC / Vinyl Badminton Flooring"): KeywordRule(
        required_any=_terms(
            "badminton flooring", "badminton court flooring",
            "badminton pvc", "badminton vinyl", "badminton mat",
        ),
        excluded_any=_terms(
            "wooden", "wood flooring", "court tile", "modular tile",
            "rubber tile",
        ),
    ),
    ("Acryplay", "Acrylic Sports Court Systems"): KeywordRule(
        required_any=_terms(
            "acrylic court", "acrylic sports", "acrylic basketball",
            "acrylic tennis", "acrylic pickleball", "acrylic badminton",
            "acrylic skating", "acrylic volleyball",
        ),
        excluded_any=_terms(
            "running track", "athletic track", "modular tile",
            "interlocking tile",
        ),
    ),
    ("Acryplay", "PP Modular Sports Court Tiles"): KeywordRule(
        required_any=_terms(
            "court tile", "sports tile", "modular tile", "pp tile",
            "interlocking court", "interlocking sports",
        ),
        excluded_any=_terms(
            "gym rubber tile", "playground rubber tile", "wooden",
            "pvc flooring", "vinyl flooring",
        ),
    ),
    ("Track & Field", "Synthetic Athletic Track Systems"): KeywordRule(
        required_any=_terms(
            "running track", "athletic track", "athletics track",
            "synthetic track", "jogging track",
        ),
        excluded_any=_terms(
            "gym sled track", "railway track", "music track",
        ),
    ),
    ("Sports Equipment", "Sports Equipment / Turnkey Facility"): KeywordRule(
        required_any=_terms(
            "sports equipment", "playground equipment",
            "basketball pole", "basketball hoop", "basketball post",
            "badminton post", "volleyball post", "tennis post",
            "football goal", "hockey goal", "cricket net",
            "sports net", "gym equipment", "turnkey sports facility",
            "sports facility equipment",
        ),
        excluded_any=_terms(
            "rubber flooring", "pvc flooring", "vinyl flooring",
            "wooden flooring", "artificial turf", "artificial grass",
            "acrylic flooring",
        ),
    ),
    ("Woodplay", "Maple / Hevea Wooden Sports Flooring"): KeywordRule(
        required_any=_terms(
            "wooden sports flooring", "sports wooden flooring",
            "wooden court flooring", "basketball wooden",
            "badminton wooden", "maple sports", "maple basketball",
            "hevea sports", "hevea flooring",
        ),
        excluded_any=_terms(
            "pvc", "vinyl", "court tile", "rubber tile",
        ),
    ),
}

MIN_KEYWORDS_PER_PRODUCT = 200


def normalize_keyword(keyword: str) -> str:
    return re.sub(r"\s+", " ", str(keyword or "")).strip().casefold()


def validate_product_keyword(
    vertical: str,
    product: str,
    keyword: str,
) -> tuple[bool, str]:
    """Return whether a keyword is semantically valid for its exact route."""
    rule = PRODUCT_KEYWORD_RULES.get((vertical, product))
    if rule is None:
        return False, "no product keyword rule configured"

    phrase = normalize_keyword(keyword)
    if not phrase:
        return False, "empty keyword"

    excluded = next(
        (term for term in rule.excluded_any if term in phrase),
        None,
    )
    if excluded:
        return False, f"contains excluded product marker: {excluded}"

    if not any(term in phrase for term in rule.required_any):
        return False, "missing required product marker"

    return True, "matched exact product route"


def validate_keyword_library(
    library: dict[str, dict[str, list[str]]],
) -> list[str]:
    """Return all route/content errors; an empty list means the library is safe."""
    errors: list[str] = []
    expected_routes = set(PRODUCT_KEYWORD_RULES)
    actual_routes = {
        (vertical, product)
        for vertical, products in library.items()
        for product in products
    }

    for vertical, product in sorted(expected_routes - actual_routes):
        errors.append(f"missing route: {vertical} / {product}")
    for vertical, product in sorted(actual_routes - expected_routes):
        errors.append(f"unknown route: {vertical} / {product}")

    globally_seen: dict[str, tuple[str, str]] = {}
    for vertical, products in library.items():
        for product, keywords in products.items():
            if len(keywords) < MIN_KEYWORDS_PER_PRODUCT:
                errors.append(
                    f"under-covered route: {vertical} / {product} has "
                    f"{len(keywords)} keywords; minimum is "
                    f"{MIN_KEYWORDS_PER_PRODUCT}"
                )
            for keyword in keywords:
                valid, reason = validate_product_keyword(
                    vertical,
                    product,
                    keyword,
                )
                if not valid:
                    errors.append(
                        f"{vertical} / {product} / {keyword}: {reason}"
                    )
                normalized = normalize_keyword(keyword)
                previous = globally_seen.get(normalized)
                if previous:
                    errors.append(
                        f"duplicate keyword '{keyword}' in "
                        f"{previous[0]} / {previous[1]} and "
                        f"{vertical} / {product}"
                    )
                else:
                    globally_seen[normalized] = (vertical, product)
    return errors
