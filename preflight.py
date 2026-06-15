"""Read-only production readiness checks for Sunzone Prospect Flow."""

from __future__ import annotations

import os
import smtplib

from config import (
    INDIA_CITY_ROTATION,
    SHEET_HEADERS,
    SHEET_ID,
    VERTICALS,
    iter_products,
)
from keyword_library import load_keyword_library
from main import SOURCE_REGISTRY
from sheets import get_client
from sku_catalog import (
    load_sku_catalog,
    sku_counts_by_vertical,
    validate_sku_routes,
)
from state import load_state


def check_static_configuration() -> list[str]:
    checks = []
    products = list(iter_products())
    library = load_keyword_library()
    sku_catalog = load_sku_catalog()

    # Intentional release guardrails. Update these values only when Sunzone
    # formally adds a vertical, product, source, or expands the town catalogue.
    if len(VERTICALS) != 8:
        raise RuntimeError(f"Expected 8 verticals, found {len(VERTICALS)}")
    if len(products) != 18:
        raise RuntimeError(
            f"Expected 18 search families, found {len(products)}"
        )
    sku_errors = validate_sku_routes(VERTICALS)
    if sku_errors:
        raise RuntimeError("Invalid SKU routes: " + "; ".join(sku_errors[:5]))
    if len(sku_catalog) != 170:
        raise RuntimeError(
            f"Expected 170 SKU/system records, found {len(sku_catalog)}"
        )
    inventory_sku_count = sum(
        record["catalogue_type"] == "SKU"
        for record in sku_catalog
    )
    website_system_count = sum(
        record["catalogue_type"] == "Website system"
        for record in sku_catalog
    )
    if (inventory_sku_count, website_system_count) != (152, 18):
        raise RuntimeError(
            "Expected 152 inventory SKUs and 18 website systems, found "
            f"{inventory_sku_count} and {website_system_count}"
        )
    sku_counts = sku_counts_by_vertical()
    missing_sku_verticals = [
        vertical for vertical in VERTICALS if not sku_counts[vertical]
    ]
    if missing_sku_verticals:
        raise RuntimeError(
            f"Verticals without SKUs: {', '.join(missing_sku_verticals)}"
        )
    if len(SOURCE_REGISTRY) != 11:
        raise RuntimeError(f"Expected 11 sources, found {len(SOURCE_REGISTRY)}")
    if len(INDIA_CITY_ROTATION) < 7705:
        raise RuntimeError(
            f"Expected at least 7,705 towns, found {len(INDIA_CITY_ROTATION)}"
        )
    if len(INDIA_CITY_ROTATION) != len(set(INDIA_CITY_ROTATION)):
        raise RuntimeError("City rotation contains duplicates")
    if INDIA_CITY_ROTATION[0] != "Mumbai, Maharashtra":
        raise RuntimeError("Maharashtra-first rotation must begin with Mumbai")
    maharashtra_count = sum(
        city.endswith(", Maharashtra")
        for city in INDIA_CITY_ROTATION
    )
    if maharashtra_count != 509:
        raise RuntimeError(
            f"Expected 509 Maharashtra towns, found {maharashtra_count}"
        )
    if not all(
        city.endswith(", Maharashtra")
        for city in INDIA_CITY_ROTATION[:maharashtra_count]
    ):
        raise RuntimeError(
            "All Maharashtra towns must be contiguous at the start"
        )
    if any(
        city.endswith(", Maharashtra")
        for city in INDIA_CITY_ROTATION[maharashtra_count:]
    ):
        raise RuntimeError("Maharashtra town found after national rotation")

    keyword_count = sum(
        len(keywords)
        for products_by_name in library.values()
        for keywords in products_by_name.values()
    )
    state = load_state()
    city_index = int(state.get("city_index", 0))
    if not 0 <= city_index < len(INDIA_CITY_ROTATION):
        raise RuntimeError(f"Invalid city rotation index: {city_index}")

    checks.extend([
        "8 verticals",
        "18 buyer-search families",
        "152 inventory SKUs and 18 website systems",
        "11 lead sources",
        f"{len(INDIA_CITY_ROTATION):,} unique towns",
        f"{maharashtra_count} Maharashtra towns first, beginning with Mumbai",
        f"{keyword_count:,} validated product keywords",
        f"valid rotation index {city_index}",
    ])
    return checks


def _repairable_header_drift(headers: list[str]) -> bool:
    """Allow one label edit, never missing or reordered sheet columns."""
    if len(headers) != len(SHEET_HEADERS):
        return False
    mismatches = sum(
        actual != expected
        for actual, expected in zip(headers, SHEET_HEADERS)
    )
    return mismatches == 1


def check_google_sheet() -> list[str]:
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheets = {worksheet.title: worksheet for worksheet in spreadsheet.worksheets()}
    checks = []

    for vertical, config in VERTICALS.items():
        tab_name = config["tab"]
        worksheet = worksheets.get(tab_name)
        if worksheet is None:
            raise RuntimeError(f"Missing Google Sheet tab: {tab_name}")
        headers = worksheet.row_values(1)
        if headers != SHEET_HEADERS:
            if not _repairable_header_drift(headers):
                raise RuntimeError(
                    f"Unsafe header structure in {tab_name}: "
                    f"expected {SHEET_HEADERS}, found {headers}"
                )
            worksheet.update("A1", [SHEET_HEADERS])
            repaired = worksheet.row_values(1)
            if repaired != SHEET_HEADERS:
                raise RuntimeError(
                    f"Could not repair headers in {tab_name}: {repaired}"
                )
            checks.append(f"{vertical}: {tab_name} header labels repaired")
            continue
        checks.append(f"{vertical}: {tab_name} accessible")
    return checks


def check_gmail_login() -> list[str]:
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not gmail_user or not gmail_password:
        raise RuntimeError("Gmail notification secrets are missing")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
        server.login(gmail_user, gmail_password)
    return [f"Gmail authentication valid for {gmail_user}"]


def main() -> int:
    checks = []
    checks.extend(check_static_configuration())
    checks.extend(check_google_sheet())
    checks.extend(check_gmail_login())
    print("SUNZONE PROSPECT FLOW PREFLIGHT: PASS")
    for check in checks:
        print(f"  PASS: {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
