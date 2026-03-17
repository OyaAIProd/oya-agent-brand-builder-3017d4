import os
import json
import time
import httpx

try:
    from google.oauth2 import credentials, service_account
    from google.auth.transport.requests import Request as AuthRequest
except ImportError:
    print(json.dumps({"error": "google-auth not installed. pip install google-auth"}))
    raise SystemExit(1)

SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
DRIVE_API = "https://www.googleapis.com/drive/v3/files"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]


def get_creds(creds_json):
    if creds_json.get("type") == "authorized_user":
        creds = credentials.Credentials.from_authorized_user_info(creds_json, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    creds.refresh(AuthRequest())
    return creds


def headers(creds):
    return {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}


def _api(method, url, creds, timeout=15, **kwargs):
    """HTTP request with exponential backoff on 429."""
    for attempt in range(4):
        with httpx.Client(timeout=timeout) as c:
            r = c.request(method, url, headers=headers(creds), **kwargs)
        if r.status_code == 429 and attempt < 3:
            time.sleep(min(2 ** attempt, 30))
            continue
        r.raise_for_status()
        return r.json()


def do_list_spreadsheets(creds, query, limit):
    q = "mimeType='application/vnd.google-apps.spreadsheet'"
    if query:
        q += f" and name contains '{query}'"
    params = {"q": q, "pageSize": min(limit, 50), "fields": "files(id,name,modifiedTime,webViewLink)"}
    data = _api("GET", DRIVE_API, creds, params=params)
    files = data.get("files", [])
    return {
        "spreadsheets": [
            {"id": f["id"], "name": f["name"], "modified": f.get("modifiedTime", ""), "url": f.get("webViewLink", "")}
            for f in files
        ],
        "count": len(files),
    }


def do_get_sheet_info(creds, spreadsheet_id):
    data = _api("GET", f"{SHEETS_API}/{spreadsheet_id}", creds,
                params={"fields": "spreadsheetId,properties.title,sheets.properties"})
    sheets = data.get("sheets", [])
    return {
        "spreadsheet_id": data.get("spreadsheetId", ""),
        "title": data.get("properties", {}).get("title", ""),
        "sheets": [
            {
                "name": s["properties"]["title"],
                "index": s["properties"]["index"],
                "row_count": s["properties"].get("gridProperties", {}).get("rowCount", 0),
                "column_count": s["properties"].get("gridProperties", {}).get("columnCount", 0),
            }
            for s in sheets
        ],
    }


def do_read_sheet(creds, spreadsheet_id, range_str):
    data = _api("GET", f"{SHEETS_API}/{spreadsheet_id}/values/{range_str}", creds)
    values = data.get("values", [])
    return {"range": data.get("range", ""), "values": values, "rows": len(values)}


def do_write_cells(creds, spreadsheet_id, range_str, values):
    if isinstance(values, str):
        values = json.loads(values)
    body = {"range": range_str, "majorDimension": "ROWS", "values": values}
    data = _api("PUT", f"{SHEETS_API}/{spreadsheet_id}/values/{range_str}", creds,
                json=body, params={"valueInputOption": "USER_ENTERED"})
    return {"updated_range": data.get("updatedRange", ""), "updated_cells": data.get("updatedCells", 0)}


def do_append_rows(creds, spreadsheet_id, range_str, values):
    if isinstance(values, str):
        values = json.loads(values)
    body = {"range": range_str, "majorDimension": "ROWS", "values": values}
    data = _api("POST", f"{SHEETS_API}/{spreadsheet_id}/values/{range_str}:append", creds,
                json=body, params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"})
    updates = data.get("updates", {})
    return {"updated_range": updates.get("updatedRange", ""), "updated_rows": updates.get("updatedRows", 0)}


def do_create_spreadsheet(creds, title, sheet_names):
    body = {"properties": {"title": title}}
    if sheet_names:
        names = [n.strip() for n in sheet_names.split(",") if n.strip()]
        body["sheets"] = [{"properties": {"title": name}} for name in names]
    data = _api("POST", SHEETS_API, creds, json=body)
    return {
        "spreadsheet_id": data["spreadsheetId"],
        "title": data["properties"]["title"],
        "url": data.get("spreadsheetUrl", ""),
        "sheets": [s["properties"]["title"] for s in data.get("sheets", [])],
    }


try:
    creds_json = json.loads(os.environ["GOOGLE_SHEETS_CREDENTIALS_JSON"])
    creds = get_creds(creds_json)
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")

    if action == "list_spreadsheets":
        result = do_list_spreadsheets(creds, inp.get("query", ""), inp.get("limit", 10))
    elif action == "get_sheet_info":
        result = do_get_sheet_info(creds, inp.get("spreadsheet_id", ""))
    elif action == "read_sheet":
        result = do_read_sheet(creds, inp.get("spreadsheet_id", ""), inp.get("range", "Sheet1"))
    elif action == "write_cells":
        result = do_write_cells(creds, inp.get("spreadsheet_id", ""), inp.get("range", "Sheet1"), inp.get("values", "[]"))
    elif action == "append_rows":
        result = do_append_rows(creds, inp.get("spreadsheet_id", ""), inp.get("range", "Sheet1"), inp.get("values", "[]"))
    elif action == "create_spreadsheet":
        result = do_create_spreadsheet(creds, inp.get("title", "Untitled"), inp.get("sheet_names", ""))
    else:
        result = {"error": f"Unknown action: {action}"}

    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
