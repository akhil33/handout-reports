#!/usr/bin/env python3
"""Ingest Rista Sync Excel data into local SQLite database.

Usage:
    python ingest.py              # Ingest from default Excel path
    python ingest.py --stats      # Show database stats after ingestion
"""
import argparse
from hangout.ingest import ingest_from_excel
from hangout.db import get_conn, DB_PATH


def show_stats():
    """Print database summary stats."""
    with get_conn() as conn:
        sales_count = conn.execute("SELECT COUNT(*) FROM daily_sales").fetchone()[0]
        trading_days = conn.execute("SELECT COUNT(*) FROM daily_sales WHERE total_net > 0").fetchone()[0]
        date_range = conn.execute(
            "SELECT MIN(date), MAX(date) FROM daily_sales WHERE total_net > 0"
        ).fetchone()
        section_count = conn.execute("SELECT COUNT(DISTINCT section) FROM section_sales").fetchone()[0]
        expense_count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        total_expenses = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0

    print(f"\n--- Database: {DB_PATH} ---")
    print(f"  Total rows:    {sales_count}")
    print(f"  Trading days:  {trading_days}")
    print(f"  Date range:    {date_range[0]} to {date_range[1]}")
    print(f"  Sections:      {section_count}")
    print(f"  Expenses:      {expense_count} items (total: Rs.{total_expenses:,.0f}/month)")


def main():
    parser = argparse.ArgumentParser(description="Ingest Rista data into local DB")
    parser.add_argument("--stats", action="store_true", help="Show DB stats after ingestion")
    args = parser.parse_args()

    print("Ingesting from Excel...")
    result = ingest_from_excel()
    print(f"  Ingested {result['sales_rows']} sales rows, {result['expenses']} expenses")

    if args.stats:
        show_stats()

    print("Done!")


if __name__ == "__main__":
    main()
