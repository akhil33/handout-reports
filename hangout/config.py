import os
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYNC_DIR = PROJECT_ROOT / "Sync"

def _find_excel():
    """Find the Rista Sync Excel file (Google Drive may add suffixes like '(1)')."""
    if SYNC_DIR.exists():
        matches = sorted(SYNC_DIR.glob("Rista Sync*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]
    return SYNC_DIR / "Rista Sync.xlsx"

EXCEL_PATH = _find_excel()

# --- Sheet names ---
SHEET_DAILY_SALES = "Daily Sales"
SHEET_EXPENSES = "Expenses Fixed"
SHEET_DASHBOARD = "Dashboard"

# --- Business sections ---
SECTIONS = [
    "AC Beverage",
    "AC Liquor",
    "Food",
    "Janatha Liquor",
    "Janatha Beverage",
    "Roof Top Liquor",
]

# --- Alert thresholds ---
MIN_PROFIT_MARGIN = 0.35          # Alert if margin drops below 35%
LOW_SALES_PERCENTILE = 0.20       # Alert if today is in bottom 20% of recent days
HIGH_SALES_PERCENTILE = 0.90      # Flag if today is in top 10% (celebration!)

# --- Rolling windows for comparisons ---
ROLLING_WINDOWS = [7, 30]

# --- Fixed monthly expenses (loaded from Excel, but defaults here as fallback) ---
DEFAULT_DAYS_IN_MONTH = 30

# --- Gmail settings ---
GMAIL_SENDER = os.environ.get("HANGOUT_GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.environ.get("HANGOUT_GMAIL_APP_PASSWORD", "")
GMAIL_RECIPIENT = os.environ.get("HANGOUT_GMAIL_RECIPIENT", "")

# --- Report settings ---
BUSINESS_NAME = "The Hangout"
CURRENCY_SYMBOL = "₹"
