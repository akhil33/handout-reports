"""Data access layer — reads from local SQLite (primary) with Excel fallback."""
import pandas as pd
from hangout.config import EXCEL_PATH, SHEET_DAILY_SALES, SHEET_EXPENSES, SECTIONS
from hangout.db import DB_PATH, get_conn


# ---------------------------------------------------------------------------
# Primary: SQLite
# ---------------------------------------------------------------------------

def load_daily_sales():
    """Load daily sales from SQLite. Falls back to Excel if DB is empty."""
    if not DB_PATH.exists():
        return _load_daily_sales_excel()

    with get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM daily_sales WHERE total_net > 0 ORDER BY date DESC",
            conn,
        )
    if df.empty:
        return _load_daily_sales_excel()

    df["Date"] = pd.to_datetime(df["date"])

    # Join section data as wide columns to match the Excel format
    with get_conn() as conn:
        sections_df = pd.read_sql_query("SELECT * FROM section_sales", conn)

    if not sections_df.empty:
        for section in SECTIONS:
            s = sections_df[sections_df["section"] == section][["date", "net", "cost", "profit"]]
            s = s.rename(columns={
                "net": f"{section} Net",
                "cost": f"{section} Cost",
                "profit": f"{section} Profit",
            })
            df = df.merge(s, left_on="date", right_on="date", how="left")

    # Rename to match expected column names
    df = df.rename(columns={
        "total_net": "Total Net",
        "total_cost": "Total Cost",
        "total_profit": "Total Profit",
        "margin_pct": "Total Margin %",
    })

    numeric_cols = df.select_dtypes(include="number").columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df


def load_expenses():
    """Load expenses from SQLite. Falls back to Excel if DB is empty."""
    if not DB_PATH.exists():
        return _load_expenses_excel()

    with get_conn() as conn:
        rows = conn.execute("SELECT name, amount FROM expenses").fetchall()

    if not rows:
        return _load_expenses_excel()

    return {row["name"]: row["amount"] for row in rows}


def get_sales_for_date(df, date):
    """Get a single day's sales row. Returns None if not found or zero-sales day."""
    date = pd.Timestamp(date).normalize()
    row = df[df["Date"].dt.normalize() == date]
    if row.empty:
        return None
    row = row.iloc[0]
    if row.get("Total Net", 0) == 0:
        return None
    return row


def get_recent_sales(df, date, days):
    """Get the last N trading days (non-zero sales) up to and including the given date."""
    date = pd.Timestamp(date).normalize()
    recent = df[(df["Date"].dt.normalize() <= date) & (df["Total Net"] > 0)]
    return recent.head(days)


def get_section_columns():
    """Return a dict mapping section name to its column name prefixes."""
    return {s: s for s in SECTIONS}


def get_mtd_sales(df, date):
    """Get all sales rows for the month containing the given date."""
    date = pd.Timestamp(date).normalize()
    month_start = date.replace(day=1)
    mtd = df[
        (df["Date"].dt.normalize() >= month_start)
        & (df["Date"].dt.normalize() <= date)
        & (df["Total Net"] > 0)
    ]
    return mtd


# ---------------------------------------------------------------------------
# Fallback: Excel (for when DB hasn't been populated yet)
# ---------------------------------------------------------------------------

def _load_daily_sales_excel(path=None):
    """Load and clean the Daily Sales sheet from Rista Sync Excel."""
    path = path or EXCEL_PATH
    df = pd.read_excel(path, sheet_name=SHEET_DAILY_SALES, engine="openpyxl")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.drop_duplicates(subset=["Date"], keep="first")
    df = df.sort_values("Date", ascending=False).reset_index(drop=True)

    numeric_cols = df.select_dtypes(include="number").columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df


def _load_expenses_excel(path=None):
    """Load fixed expenses from the Expenses Fixed sheet."""
    path = path or EXCEL_PATH
    df = pd.read_excel(path, sheet_name=SHEET_EXPENSES, engine="openpyxl")

    df = df.iloc[:, :2]
    df.columns = ["expense", "amount"]
    df = df.dropna(subset=["expense", "amount"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    return dict(zip(df["expense"], df["amount"]))
