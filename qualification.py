"""High-confidence buyer qualification for sales-ready lead output."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from config import (
    COMPETITOR_BRANDS,
    SUPPLIER_CONTEXT_SIGNALS,
    SUPPLIER_SIGNALS,
    VERTICAL_BUYER_SIGNALS,
)


def _normalize(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def identity_text(lead: dict) -> str:
    website = str(lead.get("website", ""))
    parsed = urlparse(
        website if "://" in website else f"https://{website}"
    )
    return _normalize(
        " ".join(
            (
                lead.get("company", ""),
                website,
                parsed.netloc,
                lead.get("email", ""),
            )
        )
    )


def evidence_text(lead: dict) -> str:
    return _normalize(
        f"{identity_text(lead)} {lead.get('website_text', '')}"
    )


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized = _normalize(phrase)
    return bool(normalized and re.search(rf"\b{re.escape(normalized)}\b", text))


def competitor_reasons(lead: dict) -> list[str]:
    identity = identity_text(lead)
    evidence = evidence_text(lead)
    reasons = [
        f"known competitor: {brand}"
        for brand in COMPETITOR_BRANDS
        if _contains_phrase(identity, brand)
    ]
    reasons.extend(
        f"supplier signal: {signal}"
        for signal in SUPPLIER_SIGNALS
        if _contains_phrase(identity, signal)
    )
    reasons.extend(
        f"supplier claim: {signal}"
        for signal in SUPPLIER_CONTEXT_SIGNALS
        if _contains_phrase(evidence, signal)
    )
    return reasons


def buyer_matches(lead: dict, vertical: str) -> list[str]:
    text = evidence_text(lead)
    return [
        signal
        for signal in VERTICAL_BUYER_SIGNALS.get(vertical, [])
        if _contains_phrase(text, signal)
    ]


def qualify_lead(lead: dict, vertical: str) -> tuple[bool, int, str]:
    if not str(lead.get("company", "")).strip():
        return False, 0, "missing company"
    if not str(lead.get("phone", "")).strip():
        return False, 0, "missing phone"

    blocked = competitor_reasons(lead)
    if blocked:
        return False, 0, "; ".join(blocked[:3])

    buyers = buyer_matches(lead, vertical)
    if not buyers:
        return False, 0, f"no verified {vertical} buyer signal"

    score = 65
    score += min(len(buyers), 2) * 10
    score += 5 if lead.get("website") else 0
    score += 5 if lead.get("email") else 0
    score += 5 if lead.get("contact_person") else 0
    score = min(score, 100)
    return True, score, f"{vertical} buyer signal: {', '.join(buyers[:3])}"
