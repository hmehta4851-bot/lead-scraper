"""One-shot script: archive and clear legacy/current lead tabs."""
from datetime import datetime

from config import SHEET_HEADERS, SHEET_ID, VERTICALS
from sheets import get_client
import gspread

LEGACY_TABS = [
    "EPDM Granules",
    "PU Binder",
    "Artificial Football Turf",
    "Hockey Turf",
    "Multi-Sport Turf",
    "Cricket Turf",
    "Padel Court Turf",
    "Badminton PVC Flooring",
    "Gym Rubber Roll Flooring",
    "Gym Astro Turf",
    "Wooden Sports Flooring",
    "Athletic Running Track",
    "Acrylic Sports Flooring",
    "Basketball Flooring",
    "PP Interlocking Tiles",
]


def clear_all_tabs():
    client = get_client()
    sh = client.open_by_key(SHEET_ID)
    current_tabs = [cfg["tab"] for cfg in VERTICALS.values()]
    tab_names = list(dict.fromkeys(LEGACY_TABS + current_tabs))
    archive_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for tab_name in tab_names:
        try:
            ws = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"  [{tab_name}] Tab not found — skipping")
            continue

        all_rows = ws.get_all_values()
        is_legacy = tab_name in LEGACY_TABS
        if len(all_rows) <= 1 and is_legacy:
            sh.del_worksheet(ws)
            print(f"  [{tab_name}] Removed empty legacy tab")
            continue
        if len(all_rows) <= 1:
            print(f"  [{tab_name}] Already empty")
            continue

        archive_name = f"Archive {archive_stamp} {tab_name}"[:100]
        archive = sh.add_worksheet(
            title=archive_name,
            rows=max(len(all_rows), 2),
            cols=max(len(row) for row in all_rows),
        )
        archive.update("A1", all_rows)
        print(f"  [{tab_name}] Backed up to [{archive_name}]")

        # Delete all rows except header (row 1)
        row_count = len(all_rows)
        ws.delete_rows(2, row_count)
        print(f"  [{tab_name}] Cleared {row_count - 1} rows")
        if is_legacy:
            sh.del_worksheet(ws)
            print(f"  [{tab_name}] Removed legacy tab after backup")

    for tab_name in current_tabs:
        try:
            ws = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=20)
        ws.update("A1", [SHEET_HEADERS])

    for ws in sh.worksheets():
        if ws.title.startswith("Archive "):
            try:
                ws.hide()
            except Exception:
                pass

    print("\nOnly 8 live vertical tabs remain visible; archives are hidden.")


if __name__ == "__main__":
    clear_all_tabs()
