"""Ingest data from Rista Sync Excel into local SQLite database."""
import pandas as pd
from hangout.config import EXCEL_PATH, SHEET_DAILY_SALES, SHEET_EXPENSES, SECTIONS
from hangout.db import get_conn, init_db, upsert_daily_sale, upsert_section_sale, upsert_expense


def ingest_from_excel(path=None):
    """Read Rista Sync Excel and load all data into SQLite."""
    path = path or EXCEL_PATH
    init_db()

    sales_count = _ingest_daily_sales(path)
    expense_count = _ingest_expenses(path)

    return {"sales_rows": sales_count, "expenses": expense_count}


def _ingest_daily_sales(path):
    """Ingest daily sales and section breakdowns from Excel."""
    df = pd.read_excel(path, sheet_name=SHEET_DAILY_SALES, engine="openpyxl")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.drop_duplicates(subset=["Date"], keep="first")

    numeric_cols = df.select_dtypes(include="number").columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    count = 0
    with get_conn() as conn:
        for _, row in df.iterrows():
            date_str = row["Date"].strftime("%Y-%m-%d")
            total_net = float(row.get("Total Net", 0))
            total_cost = float(row.get("Total Cost", 0))
            total_profit = float(row.get("Total Profit", 0))
            margin_pct = float(row.get("Total Margin %", 0))

            upsert_daily_sale(conn, date_str, total_net, total_cost, total_profit, margin_pct)

            # Section breakdowns
            for section in SECTIONS:
                net = float(row.get(f"{section} Net", 0))
                cost = float(row.get(f"{section} Cost", 0))
                profit = float(row.get(f"{section} Profit", 0))
                if net > 0 or cost > 0:
                    upsert_section_sale(conn, date_str, section, net, cost, profit)

            count += 1

    return count


def _ingest_expenses(path):
    """Ingest fixed expenses from Excel."""
    df = pd.read_excel(path, sheet_name=SHEET_EXPENSES, engine="openpyxl")
    df = df.iloc[:, :2]
    df.columns = ["expense", "amount"]
    df = df.dropna(subset=["expense", "amount"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    count = 0
    with get_conn() as conn:
        for _, row in df.iterrows():
            if row["amount"] > 0:
                upsert_expense(conn, str(row["expense"]).strip(), float(row["amount"]))
                count += 1

    return count
