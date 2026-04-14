#!/usr/bin/env python3
"""The Hangout — Business Dashboard"""
import sys
import threading
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

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Smart cold-start: fast first paint + background backfill
# ---------------------------------------------------------------------------
from hangout.db import DB_PATH, init_db, get_conn
from hangout.sync import sync_date_range

init_db()


def _trading_days_count():
    try:
        with get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM daily_sales WHERE total_net > 0").fetchone()[0]
    except Exception:
        return 0


def _backfill_background(start_str, end_str):
    """Run a backfill in a background thread (non-blocking)."""
    sync_date_range(start_str, end_str)


trading_count = _trading_days_count()

if trading_count == 0:
    # No data at all — quick sync last 7 days so user sees something fast
    with st.spinner("Loading recent data..."):
        end = date.today()
        start = end - timedelta(days=6)
        sync_date_range(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

    # Kick off full history backfill in background
    end = date.today() - timedelta(days=7)
    start_bg = date(2024, 8, 1)  # earliest data available
    t = threading.Thread(
        target=_backfill_background,
        args=(start_bg.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")),
        daemon=True,
    )
    t.start()
    st.toast("Loading historical data in the background...", icon="⏳")

elif trading_count < 30:
    # Has some data but not much — backfill more in background
    end = date.today() - timedelta(days=7)
    start_bg = date(2024, 8, 1)
    t = threading.Thread(
        target=_backfill_background,
        args=(start_bg.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")),
        daemon=True,
    )
    t.start()

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

st.sidebar.markdown(SIDEBAR_BRAND, unsafe_allow_html=True)
st.sidebar.markdown("")

# Quick KPIs
if not df.empty:
    trading = df[df["Total Net"] > 0]
    if not trading.empty:
        latest = trading.iloc[0]
        latest_date = latest["Date"].strftime("%b %d")
        net = latest["Total Net"]
        profit = latest["Total Profit"]
        margin = latest["Total Margin %"]

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
        st.sidebar.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

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
    if st.button("Load full history (Aug 2024+)", use_container_width=True):
        with st.spinner("Syncing all history..."):
            results = sync_date_range("2024-08-01", date.today().strftime("%Y-%m-%d"))
        ok = sum(1 for r in results if "error" not in r and r.get("net", 0) > 0)
        st.success(f"✓ {ok} trading days synced")
        st.cache_data.clear()
        st.rerun()

# Data info
if not df.empty:
    trading = df[df["Total Net"] > 0]
    if not trading.empty:
        first = trading.iloc[-1]["Date"].strftime("%b %Y")
        last = trading.iloc[0]["Date"].strftime("%b %d, %Y")
        st.sidebar.markdown(
            f'<div style="text-align:center;padding:12px 0 8px;font-size:0.68rem;color:#475569;">'
            f'{len(trading)} days &nbsp;•&nbsp; {first} — {last}</div>',
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
