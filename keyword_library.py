"""Rotating access to the checked-in Sunzone IndiaMART keyword master."""

from __future__ import annotations

import json
import re
from pathlib import Path

from config import VERTICAL_BUYER_SIGNALS
from keyword_rules import validate_keyword_library

LIBRARY_PATH = Path(__file__).with_name("keyword_library.json")
_LIBRARY_CACHE = None


def load_keyword_library() -> dict[str, dict[str, list[str]]]:
    global _LIBRARY_CACHE
    if _LIBRARY_CACHE is not None:
        return _LIBRARY_CACHE
    with LIBRARY_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("keyword_library.json must contain a vertical mapping")
    _LIBRARY_CACHE = {
        str(vertical): {
            str(product): [str(keyword) for keyword in keywords]
            for product, keywords in products.items()
        }
        for vertical, products in data.items()
    }
    errors = validate_keyword_library(_LIBRARY_CACHE)
    if errors:
        preview = "; ".join(errors[:5])
        raise ValueError(
            f"keyword_library.json failed product routing validation "
            f"({len(errors)} errors): {preview}"
        )
    return _LIBRARY_CACHE


def cursor_key(vertical: str, product: str) -> str:
    return f"{vertical}::{product}"


def select_rotating_keywords(
    vertical: str,
    product: str,
    fallback: list[str],
    cursors: dict[str, int],
    count: int = 1,
    city: str = "",
) -> tuple[list[str], int]:
    try:
        library = load_keyword_library()
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        library = {}
    keywords = library.get(vertical, {}).get(product) or fallback
    if not keywords:
        return [], 0
    key = cursor_key(vertical, product)
    start = int(cursors.get(key, 0)) % len(keywords)
    selected = [
        re.sub(
            r"\[city\]",
            city,
            keywords[(start + offset) % len(keywords)],
            flags=re.I,
        )
        for offset in range(min(count, len(keywords)))
    ]
    return selected, (start + len(selected)) % len(keywords)


def add_buyer_intent(
    vertical: str,
    keywords: list[str],
    cursor: int = 0,
) -> list[str]:
    """Pair product terms with rotating end-buyer segments."""
    signals = VERTICAL_BUYER_SIGNALS.get(vertical, [])
    if not signals:
        return keywords
    targeted = []
    for offset, keyword in enumerate(keywords):
        signal = signals[(cursor + offset) % len(signals)]
        if signal.casefold() in keyword.casefold():
            targeted.append(keyword)
        else:
            targeted.append(f"{keyword} {signal}")
    return targeted
