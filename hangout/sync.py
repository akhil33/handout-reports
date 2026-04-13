"""Sync data from Rista POS API directly into local SQLite.

No Google Sheets dependency — calls the API and writes to the DB.
"""
from datetime import date, datetime, timedelta
from hangout.rista_api import fetch_sales_summary
from hangout.db import get_conn, init_db, upsert_daily_sale, upsert_section_sale


def sync_date(target_date: str) -> dict:
    """Fetch one day's data from Rista API and store in SQLite.

    Args:
        target_date: Date string in YYYY-MM-DD format.

    Returns:
        dict with date, net, cost, profit, accounts count.
    """
    init_db()

    summary = fetch_sales_summary(target_date)
    net = summary["netAmount"]
    cost = summary["costOfGoodsSold"]
    profit = net - cost
    margin = profit / net if net > 0 else 0

    with get_conn() as conn:
        upsert_daily_sale(conn, target_date, net, cost, profit, margin)

        for acc in summary.get("accounts", []):
            upsert_section_sale(
                conn,
                target_date,
                acc["name"],
                acc["net"],
                acc["cost"],
                acc["profit"],
            )

    return {
        "date": target_date,
        "net": net,
        "cost": cost,
        "profit": profit,
        "margin": margin,
        "accounts": len(summary.get("accounts", [])),
    }


def sync_today() -> dict:
    """Sync today's data."""
    return sync_date(date.today().strftime("%Y-%m-%d"))


def sync_yesterday() -> dict:
    """Sync yesterday's data."""
    yesterday = date.today() - timedelta(days=1)
    return sync_date(yesterday.strftime("%Y-%m-%d"))


def sync_date_range(start_date: str, end_date: str) -> list:
    """Sync a range of dates (inclusive).

    Args:
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD

    Returns:
        List of result dicts for each day.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    results = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        try:
            result = sync_date(date_str)
            results.append(result)
        except Exception as e:
            results.append({"date": date_str, "error": str(e)})
        current += timedelta(days=1)

    return results
