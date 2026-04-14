#!/usr/bin/env python3
"""The Hangout — Business Dashboard"""
import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from theme import CUSTOM_CSS, SIDEBAR_BRAND, NAV_ITEMS, sidebar_kpi_card

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="The Hangout — Dashboard",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Auto-sync on cold start (Streamlit Cloud)
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
    with st.spinner("Syncing last 90 days from Rista POS..."):
        from hangout.sync import sync_date_range
        end = date.today()
        start = end - timedelta(days=89)
        results = sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        try:
            from hangout.ingest import _ingest_expenses
            from hangout.config import EXCEL_PATH
            if EXCEL_PATH.exists():
                _ingest_expenses(EXCEL_PATH)
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
from hangout.data import load_daily_sales, load_expenses


@st.cache_data(ttl=300)
def get_data():
    return load_daily_sales(), load_expenses()


df, expenses = get_data()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

# Brand
st.sidebar.markdown(SIDEBAR_BRAND, unsafe_allow_html=True)
st.sidebar.markdown("")

# Quick KPIs in sidebar
if not df.empty:
    trading = df[df["Total Net"] > 0]
    if not trading.empty:
        latest = trading.iloc[0]
        latest_date = latest["Date"].strftime("%b %d")
        net = latest["Total Net"]
        profit = latest["Total Profit"]
        margin = latest["Total Margin %"]

        # Delta vs previous day
        delta_str = None
        if len(trading) > 1:
            prev = trading.iloc[1]["Total Net"]
            if prev > 0:
                pct = (net - prev) / prev
                delta_str = f"{'+'if pct>=0 else ''}{pct:.1%} vs prev day"

        st.sidebar.markdown(
            sidebar_kpi_card(f"Sales — {latest_date}", f"₹{net/1000:.1f}K", delta_str, "#3b82f6"),
            unsafe_allow_html=True,
        )
        st.sidebar.markdown(
            '<div style="height:8px;"></div>', unsafe_allow_html=True
        )

        profit_color = "#22c55e" if margin >= 0.38 else "#f59e0b"
        st.sidebar.markdown(
            sidebar_kpi_card("Profit / Margin", f"₹{profit/1000:.1f}K  •  {margin:.1%}", None, profit_color),
            unsafe_allow_html=True,
        )

st.sidebar.markdown("")

# Navigation
st.sidebar.markdown(
    '<p style="font-size:0.65rem;color:#64748b !important;text-transform:uppercase;'
    'letter-spacing:0.12em;margin-bottom:4px;padding-left:4px;">Navigation</p>',
    unsafe_allow_html=True,
)

# Initialize session state for page
if "page" not in st.session_state:
    st.session_state.page = "Daily Overview"

page = st.sidebar.radio(
    "nav",
    list(NAV_ITEMS.keys()),
    format_func=lambda x: f"{NAV_ITEMS[x]}  {x}",
    index=list(NAV_ITEMS.keys()).index(st.session_state.page),
    label_visibility="collapsed",
    key="nav_radio",
)
st.session_state.page = page

# Sync section
st.sidebar.markdown("")
st.sidebar.markdown(
    '<p style="font-size:0.65rem;color:#64748b !important;text-transform:uppercase;'
    'letter-spacing:0.12em;margin-bottom:4px;padding-left:4px;">Data Sync</p>',
    unsafe_allow_html=True,
)

col_a, col_b = st.sidebar.columns(2)
if col_a.button("⟳ Today", use_container_width=True):
    from hangout.sync import sync_today
    try:
        result = sync_today()
        st.sidebar.success(f"✓ {result['date']}")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.sidebar.error(str(e)[:60])

if col_b.button("⟳ Yesterday", use_container_width=True):
    from hangout.sync import sync_yesterday
    try:
        result = sync_yesterday()
        st.sidebar.success(f"✓ {result['date']}")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.sidebar.error(str(e)[:60])

with st.sidebar.expander("⚙  More sync options"):
    if st.button("Backfill 30 days", use_container_width=True):
        from hangout.sync import sync_date_range
        end = date.today()
        start = end - timedelta(days=29)
        with st.spinner("Syncing..."):
            results = sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        ok = sum(1 for r in results if "error" not in r)
        st.success(f"✓ {ok} days synced")
        st.cache_data.clear()
        st.rerun()

    if st.button("Backfill 90 days", use_container_width=True):
        from hangout.sync import sync_date_range
        end = date.today()
        start = end - timedelta(days=89)
        with st.spinner("Syncing..."):
            results = sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        ok = sum(1 for r in results if "error" not in r)
        st.success(f"✓ {ok} days synced")
        st.cache_data.clear()
        st.rerun()

# Last sync info
if not df.empty:
    trading = df[df["Total Net"] > 0]
    if not trading.empty:
        last_date = trading.iloc[0]["Date"].strftime("%b %d, %Y")
        st.sidebar.markdown(
            f'<div style="text-align:center;padding:12px 0 8px;font-size:0.7rem;color:#475569;">'
            f'Latest data: {last_date}</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Route to page
# ---------------------------------------------------------------------------
if page == "Daily Overview":
    from views.daily_overview import render
    render(df, expenses)
elif page == "Trends & Analytics":
    from views.trends import render
    render(df, expenses)
elif page == "Section Performance":
    from views.sections import render
    render(df, expenses)
elif page == "Expenses & P&L":
    from views.expenses import render
    render(df, expenses)
