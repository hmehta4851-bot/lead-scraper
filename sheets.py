import gspread
from google.oauth2.service_account import Credentials
import os
import json
import time

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            os.path.join(os.path.dirname(__file__), "service_account.json"),
            scopes=SCOPES,
        )
    return gspread.authorize(creds)


def ensure_headers(ws, headers):
    existing = ws.row_values(1)
    if existing != headers:
        ws.update("A1", [headers])


def append_leads(sheet_id, tab_name, headers, leads):
    if not leads:
        return 0
    client = get_client()
    sh = client.open_by_key(sheet_id)

    try:
        ws = sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=1000, cols=len(headers))

    ensure_headers(ws, headers)

    existing_phones = set()
    try:
        all_vals = ws.get_all_values()
        phone_col = headers.index("Phone")
        for row in all_vals[1:]:
            if len(row) > phone_col and row[phone_col]:
                existing_phones.add(row[phone_col].strip())
    except Exception:
        pass

    rows_to_add = []
    for lead in leads:
        phone = str(lead.get("Phone", "")).strip()
        if phone and phone in existing_phones:
            continue
        row = [str(lead.get(h, "")) for h in headers]
        rows_to_add.append(row)
        if phone:
            existing_phones.add(phone)

    if rows_to_add:
        ws.append_rows(rows_to_add, value_input_option="USER_ENTERED")
        time.sleep(1)

    return len(rows_to_add)
