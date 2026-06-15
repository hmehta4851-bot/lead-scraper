"""Read-only canary for all Sunzone Prospect Flow lead sources."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import time
from pathlib import Path

from main import SOURCE_REGISTRY
from scrapers import browser as scraper_browser


SOURCE_GROUPS = {
    "Sulekha": "directories",
    "YellowPages": "directories",
    "JustDial": "directories",
    "DuckDuckGo": "search engines",
    "Bing": "search engines",
    "Yahoo": "search engines",
    "OpenStreetMap": "geospatial",
    "Google Maps": "geospatial",
    "ExportersIndia": "marketplaces",
    "TradeIndia": "marketplaces",
    "IndiaMART": "marketplaces",
}

SOURCE_CANARY_KEYWORDS = {
    "ExportersIndia": "artificial grass",
    "TradeIndia": "artificial grass",
    "IndiaMART": "artificial grass",
}

MIN_PRODUCTIVE_SOURCES = 2
MIN_PRODUCTIVE_GROUPS = 2

_DEGRADED_MARKERS = (
    " error:",
    " http 202",
    " http 4",
    " http 5",
    "failed after retry",
    "navigation failed",
    "likely blocked",
)


def probe_sources(
    keyword: str,
    city: str,
    source_registry=None,
    max_results: int = 3,
) -> dict:
    """Probe every source without writing to the Google Sheet."""
    registry = source_registry or SOURCE_REGISTRY
    results = []
    for source_name, search in registry:
        source_keyword = SOURCE_CANARY_KEYWORDS.get(source_name, keyword)
        started = time.monotonic()
        captured = io.StringIO()
        leads = []
        error = ""
        try:
            with contextlib.redirect_stdout(captured):
                leads = (
                    search(
                        source_keyword,
                        city,
                        max_results=max_results,
                    )
                    or []
                )
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        output = captured.getvalue().strip()
        lowered = f" {output.casefold()}"
        if error:
            status = "failed"
        elif any(marker in lowered for marker in _DEGRADED_MARKERS):
            status = "degraded"
        elif leads:
            status = "productive"
        else:
            status = "completed_zero"
        results.append(
            {
                "source": source_name,
                "group": SOURCE_GROUPS.get(source_name, "other"),
                "keyword": source_keyword,
                "status": status,
                "results": len(leads),
                "seconds": round(time.monotonic() - started, 2),
                "error": error,
                "diagnostic": output[-500:],
            }
        )

    attempted = [result["source"] for result in results]
    expected = [name for name, _ in registry]
    productive = [
        result for result in results if result["status"] == "productive"
    ]
    productive_groups = sorted({result["group"] for result in productive})
    ready = (
        attempted == expected
        and len(productive) >= MIN_PRODUCTIVE_SOURCES
        and len(productive_groups) >= MIN_PRODUCTIVE_GROUPS
    )
    return {
        "ready": ready,
        "city": city,
        "keyword": keyword,
        "attempted_count": len(attempted),
        "expected_count": len(expected),
        "productive_count": len(productive),
        "productive_groups": productive_groups,
        "sources": results,
    }


def format_report(report: dict) -> str:
    lines = [
        "# Sunzone Prospect Flow Source Readiness",
        "",
        f"- Overall: {'READY' if report['ready'] else 'DEGRADED'}",
        f"- Canary city: {report['city']}",
        f"- Canary keyword: {report['keyword']}",
        (
            f"- Sources attempted: {report['attempted_count']}/"
            f"{report['expected_count']}"
        ),
        f"- Productive sources: {report['productive_count']}",
        (
            "- Productive source groups: "
            + (", ".join(report["productive_groups"]) or "none")
        ),
        "",
        "| Source | Group | Canary | Status | Results | Seconds |",
        "|---|---|---|---:|---:|---:|",
    ]
    for source in report["sources"]:
        lines.append(
            f"| {source['source']} | {source['group']} | "
            f"{source['keyword']} | "
            f"{source['status']} | {source['results']} | "
            f"{source['seconds']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Mumbai, Maharashtra")
    parser.add_argument("--keyword", default="gym")
    parser.add_argument("--json", default="source-readiness.json")
    parser.add_argument("--markdown", default="source-readiness.md")
    args = parser.parse_args()
    try:
        report = probe_sources(args.keyword, args.city)
    finally:
        scraper_browser.close()
    Path(args.json).write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    markdown = format_report(report)
    Path(args.markdown).write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
