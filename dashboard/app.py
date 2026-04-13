#!/usr/bin/env python3
"""The Hangout — Business Dashboard

Run with: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="The Hangout",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Auto-sync: On cloud (or first run), if DB is empty, backfill from Rista API
# ---------------------------------------------------------------------------
from hangout.db import DB_PATH, init_db, get_conn

init_db()

def _db_has_data():
    try:
        with get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM daily_sales WHERE total_net > 0").fetchone()[0]
        return count > 0
    except Exception:
        return False

if not _db_has_data():
    with st.spinner("First load — syncing last 90 days from Rista POS..."):
        from hangout.sync import sync_date_range
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=89)
        results = sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        ok = sum(1 for r in results if "error" not in r)
        # Also load expenses from Excel if available
        try:
            from hangout.ingest import _ingest_expenses
            from hangout.config import EXCEL_PATH
            if EXCEL_PATH.exists():
                _ingest_expenses(EXCEL_PATH)
        except Exception:
            pass
        st.success(f"Synced {ok} days from Rista POS API")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("The Hangout")
st.sidebar.caption("Business Dashboard")

page = st.sidebar.radio(
    "Navigate",
    ["Daily Overview", "Trends & Analytics", "Section Performance", "Expenses"],
    label_visibility="collapsed",
)

# Sidebar: data sync
st.sidebar.divider()
st.sidebar.subheader("Sync Data")

col_a, col_b = st.sidebar.columns(2)
if col_a.button("Sync Today"):
    from hangout.sync import sync_today
    try:
        result = sync_today()
        st.sidebar.success(f"Synced {result['date']}: Rs.{result['net']:,.0f}")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Sync failed: {e}")

if col_b.button("Sync Yesterday"):
    from hangout.sync import sync_yesterday
    try:
        result = sync_yesterday()
        st.sidebar.success(f"Synced {result['date']}: Rs.{result['net']:,.0f}")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Sync failed: {e}")

with st.sidebar.expander("More options"):
    if st.button("Backfill Last 30 Days"):
        from hangout.sync import sync_date_range
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=29)
        with st.spinner("Syncing 30 days..."):
            results = sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        ok = sum(1 for r in results if "error" not in r)
        st.success(f"Synced {ok} of 30 days from Rista API")
        st.cache_data.clear()
        st.rerun()

    if st.button("Backfill Last 90 Days"):
        from hangout.sync import sync_date_range
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=89)
        with st.spinner("Syncing 90 days..."):
            results = sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        ok = sum(1 for r in results if "error" not in r)
        st.success(f"Synced {ok} of 90 days from Rista API")
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
from hangout.data import load_daily_sales, load_expenses

@st.cache_data(ttl=300)
def get_data():
    return load_daily_sales(), load_expenses()

df, expenses = get_data()

# Route to page
if page == "Daily Overview":
    from pages.daily_overview import render
    render(df, expenses)
elif page == "Trends & Analytics":
    from pages.trends import render
    render(df, expenses)
elif page == "Section Performance":
    from pages.sections import render
    render(df, expenses)
elif page == "Expenses":
    from pages.expenses import render
    render(df, expenses)
