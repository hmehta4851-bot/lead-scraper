"""Phone normalization and quality rules for Sunzone lead data."""

from __future__ import annotations

import re

REPEATED_DIGIT_LIMIT = 2
KNOWN_DEMO_NUMBERS = {
    "0000000000",
    "1111111111",
    "2222222222",
    "3333333333",
    "4444444444",
    "5555555555",
    "6666666666",
    "7777777777",
    "8888888888",
    "9999999999",
    "0123456789",
    "1234567890",
    "9876543210",
}


def _digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def normalize_indian_mobile(value: str) -> str:
    """Return a clean 10-digit Indian mobile number, or empty if invalid."""
    digits = _digits(value)
    if digits.startswith("0091"):
        digits = digits[4:]
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    if len(digits) != 10:
        return ""
    if digits[0] not in "6789":
        return ""
    if len(set(digits)) <= REPEATED_DIGIT_LIMIT:
        return ""
    if digits in KNOWN_DEMO_NUMBERS:
        return ""
    return digits


def classify_phone(value: str) -> tuple[str, str, str]:
    """Classify a raw phone value for audits and plain-language reports."""
    raw_digits = _digits(value)
    mobile = normalize_indian_mobile(value)
    if mobile:
        return "valid_mobile", mobile, "10-digit Indian mobile pattern"
    if not str(value or "").strip():
        return "invalid", raw_digits, "missing phone"
    if len(raw_digits) < 10:
        return "invalid", raw_digits, f"too short ({len(raw_digits)} digits)"
    if len(raw_digits) > 12:
        return "invalid", raw_digits, f"too long ({len(raw_digits)} digits)"
    last_ten = raw_digits[-10:]
    if len(last_ten) == 10 and last_ten[0] in "2345":
        return "landline_or_service", last_ten, "10-digit non-mobile pattern"
    if len(last_ten) == 10 and last_ten in KNOWN_DEMO_NUMBERS:
        return "invalid", last_ten, "known fake/demo number pattern"
    return "invalid", last_ten or raw_digits, "not a valid Indian mobile"
