"""Direct Rista POS API client.

Ports the JWT HS256 auth from the Google Apps Script to Python.
Fetches sales data directly — no Google Sheets dependency.
"""
import os
import json
import time
import uuid
import hmac
import hashlib
import base64
import urllib.request
import urllib.parse
from pathlib import Path


def _load_env():
    """Load credentials from .env file or Streamlit secrets (for cloud deployment)."""
    # Try Streamlit secrets first (cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for key in ["RISTA_API_KEY", "RISTA_API_SECRET", "RISTA_BASE_URL", "RISTA_BRANCH"]:
                if key in st.secrets:
                    os.environ.setdefault(key, st.secrets[key])
    except Exception:
        pass

    # Then try local .env file
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

_load_env()

API_KEY = os.environ.get("RISTA_API_KEY", "")
API_SECRET = os.environ.get("RISTA_API_SECRET", "")
BASE_URL = os.environ.get("RISTA_BASE_URL", "https://api.ristaapps.com/v1")
BRANCH = os.environ.get("RISTA_BRANCH", "HYD")


def _base64url_encode(data: bytes) -> str:
    """Base64 URL encode (JWT-safe, no padding)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_jwt() -> str:
    """Generate JWT token for Rista API auth (HS256), matching the Apps Script implementation."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": API_KEY,
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
    }

    encoded_header = _base64url_encode(json.dumps(header).encode())
    encoded_payload = _base64url_encode(json.dumps(payload).encode())

    signature_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        API_SECRET.encode(),
        signature_input.encode(),
        hashlib.sha256,
    ).digest()
    encoded_signature = _base64url_encode(signature)

    return f"{signature_input}.{encoded_signature}"


def api_request(endpoint: str, params: dict = None) -> dict:
    """Make authenticated GET request to Rista API."""
    if not API_KEY or not API_SECRET:
        raise ValueError(
            "Rista API credentials not configured. "
            "Create a .env file with RISTA_API_KEY and RISTA_API_SECRET"
        )

    token = _generate_jwt()

    url = BASE_URL + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={
        "x-api-key": API_KEY,
        "x-api-token": token,
        "Content-Type": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return {"status": resp.status, "data": data, "error": None}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else str(e)
        return {"status": e.code, "data": None, "error": body}
    except urllib.error.URLError as e:
        return {"status": 0, "data": None, "error": str(e.reason)}


# ---------------------------------------------------------------------------
# Account name cleaning (matches Apps Script logic)
# ---------------------------------------------------------------------------

_SKIP_NAMES = {"COGS", "Net", "Gross", "Profit", "Margin", "Total", "Amount"}


def _clean_account_name(name: str) -> str:
    """Clean account name — remove COGS suffixes and invalid entries."""
    if not name:
        return ""
    if "-COGS" in name or "COGS%" in name or "%" in name:
        return ""
    for skip in _SKIP_NAMES:
        if name == skip or name.endswith(f" {skip}"):
            return ""
    return name.strip()


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_sales_summary(date: str) -> dict:
    """Fetch sales data for a date (YYYY-MM-DD) from the summary endpoint.

    The summary endpoint returns:
    - Top-level: netAmount, costOfGoodsSold
    - accounts[]: {name, amount} — includes separate entries for COGS:
        "AC Liquor"       → net sales
        "AC Liquor-COGS"  → cost of goods
        "AC Liquor-COGS%" → margin % (ignored)

    We pair these up into a clean {name, net, cost, profit} structure.
    """
    result = api_request("/analytics/sales/summary", {"branch": BRANCH, "period": date})
    if result["status"] != 200:
        raise ConnectionError(
            f"Rista API error {result['status']}: {result['error']}"
        )

    data = result["data"]
    return _parse_summary(data)


def _parse_summary(data: dict) -> dict:
    """Parse the summary endpoint response into clean account-level data.

    The accounts list has entries like:
        {name: "AC Liquor",      amount: 71501.30}  ← net sales
        {name: "AC Liquor-COGS", amount: 39119.71}  ← cost
        {name: "AC Liquor-COGS%", amount: 55}        ← margin % (skip)
    """
    raw_accounts = data.get("accounts", [])

    # Build lookup: collect net sales and COGS separately
    net_sales = {}   # "AC Liquor" → 71501.30
    cogs = {}        # "AC Liquor" → 39119.71

    for entry in raw_accounts:
        name = (entry.get("name") or "").strip()
        amount = float(entry.get("amount") or 0)

        if not name:
            continue
        if name.endswith("-COGS%"):
            continue  # skip percentage entries
        if name.endswith("-COGS"):
            base_name = name[:-5]  # remove "-COGS"
            cogs[base_name] = amount
        else:
            net_sales[name] = amount

    # Merge into account records
    all_names = sorted(set(net_sales.keys()) | set(cogs.keys()))
    accounts = []
    for name in all_names:
        net = net_sales.get(name, 0)
        cost = cogs.get(name, 0)
        accounts.append({
            "name": name,
            "net": net,
            "cost": cost,
            "profit": net - cost,
        })

    return {
        "netAmount": float(data.get("netAmount", 0)),
        "costOfGoodsSold": float(data.get("costOfGoodsSold", 0)),
        "accounts": accounts,
        "noOfSales": data.get("noOfSales", 0),
        "avgSaleAmount": data.get("avgSaleAmount", 0),
    }
