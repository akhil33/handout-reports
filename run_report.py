#!/usr/bin/env python3
"""The Hangout — Daily Report Generator

Usage:
    python run_report.py              # Send today's report via email
    python run_report.py --preview    # Open report in browser (no email)
    python run_report.py --date 2026-04-10           # Report for a specific date
    python run_report.py --date 2026-04-10 --preview # Preview a specific date
"""
import argparse
import tempfile
import webbrowser
from datetime import date

from hangout.data import load_daily_sales, load_expenses
from hangout.analytics import full_report_data
from hangout.report import build_html_report
from hangout.mailer import send_email
from hangout.config import BUSINESS_NAME


def main():
    parser = argparse.ArgumentParser(description=f"{BUSINESS_NAME} Daily Report")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Report date in YYYY-MM-DD format (default: latest available date)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open report in browser instead of sending email",
    )
    args = parser.parse_args()

    print(f"Loading sales data...")
    df = load_daily_sales()
    expenses = load_expenses()

    if args.date:
        report_date = args.date
    else:
        # Use the most recent date with non-zero sales
        recent = df[df["Total Net"] > 0]
        if recent.empty:
            print("No sales data found.")
            return
        report_date = recent.iloc[0]["Date"]

    print(f"Generating report for {report_date}...")
    data = full_report_data(df, report_date, expenses)

    if data["today"] is None:
        print(f"No sales data for {report_date}. Skipping.")
        return

    html = build_html_report(data)

    if args.preview:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(html)
            path = f.name
        print(f"Opening preview in browser: {path}")
        webbrowser.open(f"file://{path}")
    else:
        date_str = data["today"]["date"].strftime("%b %d, %Y")
        subject = f"{BUSINESS_NAME} — Daily Report — {date_str}"
        send_email(subject, html)
        print("Done!")


if __name__ == "__main__":
    main()
