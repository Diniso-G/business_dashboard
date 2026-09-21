import re
import io
import requests
import pandas as ps
from datetime import datetime

def import_google_sheet(sheet_url: str) -> ps.DataFrame:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not match:
        raise ValueError("That doesn't look like a Google Sheets URL")
    sheet_id = match.group(1)
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    resp = requests.get(export_url, timeout=15)
    if resp.status_code != 200:
        raise ValueError("Couldn't read that sheet, make sure sharing is set to 'Anyone with the link can view'.")

    return ps.read_csv(io.StringIO(resp.text))

def import_stripe(secret_key: str, start_date: str | None = None, end_date: str | None = None) -> ps.DataFrame:
    params = {"limit": 100}
    if start_date:
        params["created[gte]"] = int(datetime.fromisoformat(start_date).timestamp())
    if end_date:
        params["created[lte]"] = int(datetime.fromisoformat(end_date).timestamp())

    rows = []
    url = "https://api.stripe.com/v1/charges"
    while url:
        resp = requests.get(url, params=params, auth=(secret_key, ""), timeout=15)
        if resp.status_code != 200:
            raise ValueError(F"Stripe API error: {resp.json().get('error', {}).get('message', resp.text)}")

        data = resp.json()
        for charge in data.get('data', []):
            if not charge.get('paid'):
                continue
            rows.append({
                "date": datetime.utcfromtimestamp(charge["created"]).strftime("%Y-%m-%d"),
                "product": (charge.get("description") or "Stripe charge"),
                "units": 1,
                "revenue": charge["amount"] / 100.0,
                "status": "refunded" if charge.get("refunded") else "paid",
                "customer": charge.get("customer") or charge.get("receipt_email") or "unknown",
            })
        params = {}
        url = None
        if data.get("has_more") and rows:
            url = f"https://api.stripe.com/v1/charges?limit=100&string_after={data['data'][-1]['id']}"
    return ps.DataFrame(rows)

def import_shopify(shop_domain: str, access_token: str, start_date: str | None = None, end_date: str | None = None) -> ps.DataFrame:
    url = f"https://{shop_domain}/admin/api/2024-01/orders.json"
    params = {"status": "any", "limit": 250}
    if start_date:
        params["created_at_min"] = start_date
    if end_date:
        params["created_at_max"] = end_date

    resp = requests.get(url, params=params, headers={"X-Shopify-Access-Token": access_token}, timeout=15)
    if resp.status_code != 200:
        raise ValueError(f"Shopify API error ({resp.status_code}): {resp.text}")

    orders = resp.json().get("orders", [])
    rows = []
    for order in orders:
        created = order.get("created_at", "")[:10]
        customer = (order.get("customer") or {}).get("email", "unknown")
        status = "refunded" if order.get("financial_status") == "refunded" else "paid"
        for item in order.get("line_items", []):
            rows.append({
                "date": created,
                "product": item.get("name", "Unknown product"),
                "units": item.get("quantity", 1),
                "revenue": float(item.get("price", 0)) * item.get("quantity", 1),
                "status": status,
                "customer": customer,
            })
    return ps.DataFrame(rows)


