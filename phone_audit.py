"""Read-only phone quality audit for the live Sunzone lead sheet."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from config import SHEET_ID, VERTICALS
from sheets import get_client


OUTPUT_JSON = Path("phone-audit.json")
OUTPUT_MD = Path("phone-audit.md")
OUTPUT_CSV = Path("phone-audit-invalid.csv")

FAKE_NUMBERS = {
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


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if digits.startswith("0091"):
        digits = digits[4:]
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    return digits[-10:] if len(digits) >= 10 else digits


def classify_phone(value: str) -> tuple[str, str, str]:
    raw = str(value or "").strip()
    digits = normalize_phone(raw)
    if not raw:
        return "invalid", digits, "missing phone"
    if len(digits) != 10:
        return "invalid", digits, f"not 10 digits after normalization ({len(digits)})"
    if digits in FAKE_NUMBERS:
        return "invalid", digits, "known fake/demo number pattern"
    if len(set(digits)) <= 2:
        return "invalid", digits, "too many repeated digits"
    if digits[0] in "6789":
        return "valid_mobile", digits, "10-digit Indian mobile pattern"
    if digits[0] in "2345":
        return "landline_or_service", digits, "10-digit non-mobile pattern; may need manual call check"
    return "invalid", digits, "invalid Indian phone starting digit"


def audit_sheet() -> dict:
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheets = {worksheet.title: worksheet for worksheet in spreadsheet.worksheets()}

    rows = []
    summary = Counter()
    by_tab = defaultdict(Counter)
    by_source = defaultdict(Counter)
    duplicate_phones = Counter()

    for vertical, config in VERTICALS.items():
        tab_name = config["tab"]
        worksheet = worksheets.get(tab_name)
        if worksheet is None:
            continue
        values = worksheet.get_all_values()
        if not values:
            continue
        headers = values[0]
        indexes = {name: index for index, name in enumerate(headers)}
        phone_index = indexes.get("Phone")
        source_index = indexes.get("Source")
        company_index = indexes.get("Company")
        city_index = indexes.get("City")
        date_index = indexes.get("Date")
        product_index = indexes.get("Product")
        if phone_index is None:
            continue

        for row_number, row in enumerate(values[1:], start=2):
            phone = row[phone_index] if len(row) > phone_index else ""
            status, normalized, reason = classify_phone(phone)
            source = (
                row[source_index].strip()
                if source_index is not None and len(row) > source_index
                else "Unknown"
            ) or "Unknown"
            company = (
                row[company_index].strip()
                if company_index is not None and len(row) > company_index
                else ""
            )
            city = (
                row[city_index].strip()
                if city_index is not None and len(row) > city_index
                else ""
            )
            date_value = (
                row[date_index].strip()
                if date_index is not None and len(row) > date_index
                else ""
            )
            product = (
                row[product_index].strip()
                if product_index is not None and len(row) > product_index
                else ""
            )

            summary[status] += 1
            by_tab[tab_name][status] += 1
            by_source[source][status] += 1
            if normalized:
                duplicate_phones[normalized] += 1

            if status != "valid_mobile":
                rows.append(
                    {
                        "tab": tab_name,
                        "row": row_number,
                        "date": date_value,
                        "city": city,
                        "company": company,
                        "product": product,
                        "source": source,
                        "phone": phone,
                        "normalized": normalized,
                        "status": status,
                        "reason": reason,
                    }
                )

    duplicate_count = sum(1 for _, count in duplicate_phones.items() if count > 1)
    audit = {
        "summary": dict(summary),
        "total_rows_with_phone_checked": sum(summary.values()),
        "duplicate_phone_values": duplicate_count,
        "by_tab": {tab: dict(counts) for tab, counts in by_tab.items()},
        "by_source": {source: dict(counts) for source, counts in by_source.items()},
        "non_mobile_or_invalid_rows": rows,
    }
    return audit


def write_outputs(audit: dict) -> None:
    OUTPUT_JSON.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "tab",
            "row",
            "date",
            "city",
            "company",
            "product",
            "source",
            "phone",
            "normalized",
            "status",
            "reason",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit["non_mobile_or_invalid_rows"])

    summary = Counter(audit["summary"])
    total = audit["total_rows_with_phone_checked"]
    valid = summary.get("valid_mobile", 0)
    landline = summary.get("landline_or_service", 0)
    invalid = summary.get("invalid", 0)
    valid_pct = int(valid / total * 100) if total else 0

    lines = [
        "# Sunzone Prospect Flow Phone Audit",
        "",
        f"- Total rows checked: {total}",
        f"- Valid Indian mobile format: {valid} ({valid_pct}%)",
        f"- Landline/service/non-mobile pattern: {landline}",
        f"- Invalid/suspicious phone values: {invalid}",
        f"- Duplicate phone values found across sheet: {audit['duplicate_phone_values']}",
        "",
        "## Meaning",
        "",
        "- `valid_mobile` means 10 digits and starts with 6, 7, 8, or 9.",
        "- `landline_or_service` may still be callable, but it is not a clean Indian mobile pattern.",
        "- `invalid` means missing, fake/demo-like, repeated, wrong length, or invalid start digit.",
        "",
        "## By Tab",
        "",
        "| Tab | Valid mobile | Landline/service | Invalid |",
        "|---|---:|---:|---:|",
    ]
    for tab, counts in sorted(audit["by_tab"].items()):
        counter = Counter(counts)
        lines.append(
            f"| {tab} | {counter.get('valid_mobile', 0)} | "
            f"{counter.get('landline_or_service', 0)} | "
            f"{counter.get('invalid', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Top Sources With Invalid Or Non-Mobile Rows",
            "",
            "| Source | Valid mobile | Landline/service | Invalid |",
            "|---|---:|---:|---:|",
        ]
    )
    ranked_sources = sorted(
        audit["by_source"].items(),
        key=lambda item: (
            Counter(item[1]).get("invalid", 0)
            + Counter(item[1]).get("landline_or_service", 0)
        ),
        reverse=True,
    )
    for source, counts in ranked_sources[:15]:
        counter = Counter(counts)
        if counter.get("invalid", 0) or counter.get("landline_or_service", 0):
            lines.append(
                f"| {source} | {counter.get('valid_mobile', 0)} | "
                f"{counter.get('landline_or_service', 0)} | "
                f"{counter.get('invalid', 0)} |"
            )
    lines.extend(
        [
            "",
            "Detailed rows are in `phone-audit-invalid.csv`.",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    audit = audit_sheet()
    write_outputs(audit)
    print(OUTPUT_MD.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
