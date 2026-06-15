import gspread
from google.oauth2.service_account import Credentials
import os
import json
import time
from collections import Counter

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    # 1. Service account JSON from env (GitHub Actions secret or local .env)
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds)

    # 2. Service account JSON file (local dev)
    sa_file = os.path.join(os.path.dirname(__file__), "service_account.json")
    if os.path.exists(sa_file):
        creds = Credentials.from_service_account_file(sa_file, scopes=SCOPES)
        return gspread.authorize(creds)

    # 3. Application Default Credentials (Workload Identity Federation / gcloud auth)
    import google.auth
    creds, _ = google.auth.default(scopes=SCOPES)
    return gspread.authorize(creds)


def ensure_headers(ws, headers):
    existing = ws.row_values(1)
    if existing[:len(headers)] != headers:
        ws.update("A1", [headers])


def load_existing_phones(sheet_id, tab_names):
    client = get_client()
    sh = client.open_by_key(sheet_id)
    phones = set()
    for tab_name in dict.fromkeys(tab_names):
        try:
            ws = sh.worksheet(tab_name)
            values = ws.get_all_values()
            headers = values[0] if values else []
            if "Phone" not in headers:
                continue
            phone_col = headers.index("Phone")
            for row in values[1:]:
                if len(row) > phone_col:
                    phone = _normalize_phone(row[phone_col])
                    if phone:
                        phones.add(phone)
        except gspread.exceptions.WorksheetNotFound:
            continue
    return phones


def load_daily_snapshot(sheet_id, tab_names, run_date, city=None):
    """Load dedupe phones plus today's per-vertical/source counts in one pass."""
    client = get_client()
    sh = client.open_by_key(sheet_id)
    worksheets = {ws.title: ws for ws in sh.worksheets()}
    phones = set()
    vertical_counts = Counter()
    vertical_source_counts = {}

    for tab_name in dict.fromkeys(tab_names):
        ws = worksheets.get(tab_name)
        if ws is None:
            continue
        values = ws.get_all_values()
        if not values:
            continue
        headers = values[0]
        indexes = {name: headers.index(name) for name in headers}
        phone_col = indexes.get("Phone")
        date_col = indexes.get("Date")
        city_col = indexes.get("City")
        vertical_col = indexes.get("Vertical")
        source_col = indexes.get("Source")

        for row in values[1:]:
            if phone_col is not None and len(row) > phone_col:
                phone = _normalize_phone(row[phone_col])
                if phone:
                    phones.add(phone)
            if (
                date_col is None
                or city_col is None
                or vertical_col is None
                or len(row) <= max(date_col, city_col, vertical_col)
                or row[date_col] != str(run_date)
                or (
                    city is not None
                    and _normalize_city(row[city_col]) != _normalize_city(city)
                )
            ):
                continue
            vertical = row[vertical_col].strip()
            if not vertical:
                continue
            vertical_counts[vertical] += 1
            source = (
                row[source_col].strip()
                if source_col is not None and len(row) > source_col
                else "Unknown"
            ) or "Unknown"
            vertical_source_counts.setdefault(vertical, Counter())[source] += 1

    return phones, vertical_counts, vertical_source_counts


def _normalize_phone(value):
    return "".join(c for c in str(value) if c.isdigit())[-10:]


def _normalize_city(value):
    return str(value).partition(",")[0].strip().casefold()


def append_leads(
    sheet_id,
    tab_name,
    headers,
    leads,
    dedupe_tabs=None,
    existing_phones=None,
):
    if not leads:
        return []
    client = get_client()
    sh = client.open_by_key(sheet_id)

    try:
        ws = sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=1000, cols=len(headers))

    ensure_headers(ws, headers)

    if existing_phones is None:
        existing_phones = load_existing_phones(
            sheet_id,
            dedupe_tabs or [tab_name],
        )

    rows_to_add = []
    accepted_leads = []
    accepted_phones = []
    for lead in leads:
        phone = _normalize_phone(lead.get("Phone", ""))
        if phone and phone in existing_phones:
            continue
        row = [str(lead.get(h, "")) for h in headers]
        rows_to_add.append(row)
        accepted_leads.append(lead)
        if phone:
            accepted_phones.append(phone)

    if rows_to_add:
        ws.append_rows(rows_to_add, value_input_option="USER_ENTERED")
        existing_phones.update(accepted_phones)
        time.sleep(1)

    return accepted_leads
