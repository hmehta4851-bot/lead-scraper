"""One-shot script: clear all lead data from all tabs, keep headers."""
from config import SHEET_ID, PRODUCTS, SHEET_HEADERS
from sheets import get_client
import gspread


def clear_all_tabs():
    client = get_client()
    sh = client.open_by_key(SHEET_ID)

    for product_name, cfg in PRODUCTS.items():
        tab_name = cfg["tab"]
        try:
            ws = sh.worksheet(tab_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"  [{tab_name}] Tab not found — skipping")
            continue

        all_rows = ws.get_all_values()
        if len(all_rows) <= 1:
            print(f"  [{tab_name}] Already empty")
            continue

        # Delete all rows except header (row 1)
        row_count = len(all_rows)
        ws.delete_rows(2, row_count)
        print(f"  [{tab_name}] Cleared {row_count - 1} rows")

    print("\nAll tabs cleared. Ready for fresh start.")


if __name__ == "__main__":
    clear_all_tabs()
