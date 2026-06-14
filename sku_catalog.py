"""Validated access to every Sunzone SKU and named website system."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


CATALOG_PATH = Path(__file__).with_name("sku_catalog.json")


def load_sku_catalog() -> list[dict[str, str]]:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    records = data.get("skus", [])
    if data.get("sku_count") != len(records):
        raise ValueError("SKU catalogue count does not match its records")
    required = {
        "vertical",
        "search_family",
        "item_name",
        "sku",
        "display_name",
        "source_url",
        "catalogue_type",
    }
    seen = set()
    for record in records:
        missing = required - set(record)
        if missing:
            raise ValueError(f"SKU record is missing fields: {sorted(missing)}")
        key = (
            record["vertical"].casefold(),
            record["display_name"].casefold(),
        )
        if key in seen:
            raise ValueError(f"Duplicate SKU route: {record['display_name']}")
        seen.add(key)
    return records


def validate_sku_routes(verticals: dict) -> list[str]:
    errors = []
    for record in load_sku_catalog():
        vertical = record["vertical"]
        family = record["search_family"]
        if vertical not in verticals:
            errors.append(f"Unknown SKU vertical: {vertical}")
            continue
        if family not in verticals[vertical]["products"]:
            errors.append(f"Unknown SKU family: {vertical} / {family}")
    return errors


def sku_counts_by_vertical() -> Counter:
    return Counter(record["vertical"] for record in load_sku_catalog())


def skus_for_family(vertical: str, family: str) -> list[dict[str, str]]:
    return [
        record
        for record in load_sku_catalog()
        if record["vertical"] == vertical
        and record["search_family"] == family
    ]


def select_rotating_sku(
    vertical: str,
    family: str,
    cursors: dict[str, int],
) -> dict[str, str]:
    records = skus_for_family(vertical, family)
    if not records:
        return {
            "vertical": vertical,
            "search_family": family,
            "item_name": family,
            "sku": family,
            "display_name": family,
            "source_url": "",
            "catalogue_type": "Search family fallback",
        }
    key = f"{vertical}::{family}"
    index = int(cursors.get(key, 0)) % len(records)
    cursors[key] = (index + 1) % len(records)
    return records[index]


def format_sku_target(record: dict[str, str]) -> str:
    """Keep buyer intent and promoted SKU distinct in the sales sheet."""
    return (
        f"{record['search_family']} | "
        f"SKU target: {record['display_name']}"
    )
