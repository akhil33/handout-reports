#!/usr/bin/env python3
"""Sync data from Rista POS API directly into local SQLite.

Usage:
    python sync.py                             # Sync today
    python sync.py --yesterday                 # Sync yesterday
    python sync.py --date 2026-04-12           # Sync specific date
    python sync.py --range 2026-04-01 2026-04-12  # Sync date range
    python sync.py --backfill 30               # Sync last 30 days
    python sync.py --stats                     # Show DB stats
"""
import argparse
from datetime import date, timedelta
from hangout.sync import sync_date, sync_today, sync_yesterday, sync_date_range
from hangout.db import get_conn, DB_PATH, init_db


def show_stats():
    """Print database summary."""
    init_db()
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM daily_sales").fetchone()[0]
        trading = conn.execute("SELECT COUNT(*) FROM daily_sales WHERE total_net > 0").fetchone()[0]
        date_range = conn.execute(
            "SELECT MIN(date), MAX(date) FROM daily_sales WHERE total_net > 0"
        ).fetchone()
        sections = conn.execute("SELECT COUNT(DISTINCT section) FROM section_sales").fetchone()[0]
        expenses = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]

        # Latest 5 days
        recent = conn.execute(
            "SELECT date, total_net, total_profit, margin_pct "
            "FROM daily_sales WHERE total_net > 0 ORDER BY date DESC LIMIT 5"
        ).fetchall()

    print(f"\n--- Database: {DB_PATH} ---")
    print(f"  Total rows:    {total}")
    print(f"  Trading days:  {trading}")
    if date_range[0]:
        print(f"  Date range:    {date_range[0]} to {date_range[1]}")
    print(f"  Sections:      {sections}")
    print(f"  Expenses:      {expenses}")
    print(f"\n  Recent days:")
    for r in recent:
        print(f"    {r[0]}  Net: Rs.{r[1]:>10,.0f}  Profit: Rs.{r[2]:>10,.0f}  Margin: {r[3]:.1%}")


def main():
    parser = argparse.ArgumentParser(description="Sync Rista POS → SQLite")
    parser.add_argument("--date", type=str, help="Sync specific date (YYYY-MM-DD)")
    parser.add_argument("--yesterday", action="store_true", help="Sync yesterday")
    parser.add_argument("--range", nargs=2, metavar=("START", "END"), help="Sync date range")
    parser.add_argument("--backfill", type=int, metavar="DAYS", help="Sync last N days")
    parser.add_argument("--stats", action="store_true", help="Show DB stats")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    if args.date:
        print(f"Syncing {args.date}...")
        result = sync_date(args.date)
        _print_result(result)

    elif args.yesterday:
        print("Syncing yesterday...")
        result = sync_yesterday()
        _print_result(result)

    elif args.range:
        start, end = args.range
        print(f"Syncing {start} to {end}...")
        results = sync_date_range(start, end)
        for r in results:
            _print_result(r)
        print(f"\nSynced {len(results)} days")

    elif args.backfill:
        end = date.today()
        start = end - timedelta(days=args.backfill - 1)
        print(f"Backfilling {args.backfill} days ({start} to {end})...")
        results = sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        ok = sum(1 for r in results if "error" not in r)
        errors = sum(1 for r in results if "error" in r)
        print(f"\nDone: {ok} synced, {errors} errors")

    else:
        print("Syncing today...")
        result = sync_today()
        _print_result(result)

    show_stats()


def _print_result(result):
    if "error" in result:
        print(f"  {result['date']}: ERROR - {result['error']}")
    else:
        print(f"  {result['date']}: Net=Rs.{result['net']:,.0f}  Profit=Rs.{result['profit']:,.0f}  Margin={result['margin']:.1%}  ({result['accounts']} sections)")


if __name__ == "__main__":
    main()
