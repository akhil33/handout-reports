"""Daily Overview page — today's KPIs, section breakdown, comparisons."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.analytics import (
    today_summary, section_breakdown, compare_averages,
    same_day_last_week, mtd_summary, expense_summary, generate_alerts,
)
from hangout.config import CURRENCY_SYMBOL


def _fmt(val):
    if val >= 100000:
        return f"{CURRENCY_SYMBOL}{val/100000:.2f}L"
    elif val >= 1000:
        return f"{CURRENCY_SYMBOL}{val/1000:.1f}K"
    return f"{CURRENCY_SYMBOL}{val:,.0f}"


def render(df, expenses):
    # Date picker — default to latest
    available_dates = df[df["Total Net"] > 0]["Date"].dt.date.tolist()
    if not available_dates:
        st.warning("No sales data available.")
        return

    selected_date = st.date_input(
        "Report Date",
        value=available_dates[0],
        min_value=available_dates[-1],
        max_value=available_dates[0],
    )

    today = today_summary(df, selected_date)
    if today is None:
        st.warning(f"No sales data for {selected_date}")
        return

    # Alerts
    alerts = generate_alerts(df, selected_date, expenses)
    for level, msg in alerts:
        if level == "warning":
            st.warning(msg)
        else:
            st.success(msg)

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)

    comparisons = compare_averages(df, selected_date)
    delta_7d = None
    if comparisons:
        delta_7d = comparisons[0]["pct_change"]

    col1.metric(
        "Sales",
        _fmt(today["total_net"]),
        f"{delta_7d:+.1%} vs 7d avg" if delta_7d else None,
    )
    col2.metric("Profit", _fmt(today["total_profit"]))
    col3.metric("Cost", _fmt(today["total_cost"]))
    col4.metric(
        "Margin",
        f"{today['margin_pct']:.1%}",
        delta_color="normal",
    )

    st.divider()

    # Two-column layout: sections + comparisons
    left, right = st.columns([3, 2])

    with left:
        st.subheader("Sales by Section")
        sections = section_breakdown(df, selected_date)
        if sections:
            sec_df = pd.DataFrame(sections)
            sec_df = sec_df[sec_df["net"] > 0]

            fig = px.pie(
                sec_df,
                values="net",
                names="name",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_traces(textinfo="label+percent", textposition="outside")
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=320,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Table
            for s in sections:
                if s["net"] > 0:
                    cols = st.columns([3, 2, 2, 1])
                    cols[0].write(f"**{s['name']}**")
                    cols[1].write(f"{_fmt(s['net'])}")
                    cols[2].write(f"{_fmt(s['profit'])}")
                    cols[3].write(f"{s['share_pct']:.0%}")

    with right:
        st.subheader("Comparisons")

        for c in comparisons:
            change = c["pct_change"]
            arrow = "up" if change > 0 else "down"
            color = "green" if change > 0 else "red"
            st.metric(
                f"{c['window']}-Day Average",
                _fmt(c["avg_sales"]),
                f"{change:+.1%}",
            )

        lw = same_day_last_week(df, selected_date)
        if lw:
            st.metric(
                f"Last {lw['last_week_date'].strftime('%A')}",
                _fmt(lw["last_week_sales"]),
                f"{lw['pct_change']:+.1%}",
            )

    st.divider()

    # MTD
    mtd = mtd_summary(df, selected_date)
    if mtd:
        st.subheader(f"Month-to-Date ({mtd['trading_days']} of {mtd['days_in_month']} days)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("MTD Sales", _fmt(mtd["total_sales"]))
        c2.metric("MTD Profit", _fmt(mtd["total_profit"]))
        c3.metric("Daily Average", _fmt(mtd["daily_avg"]))
        c4.metric("Projected Month", _fmt(mtd["projected_monthly"]))

        # Progress bar
        progress = mtd["trading_days"] / mtd["days_in_month"]
        st.progress(progress, text=f"{mtd['days_remaining']} days remaining")

    # Expense context
    exp = expense_summary(expenses)
    st.divider()
    e1, e2, e3 = st.columns(3)
    e1.metric("Monthly Fixed Expenses", _fmt(exp["total_monthly"]))
    e2.metric("Daily Burn Rate", _fmt(exp["daily_burn"]))
    net_after_fixed = today["total_profit"] - exp["daily_burn"]
    e3.metric(
        "Net After Fixed Costs",
        _fmt(abs(net_after_fixed)),
        "Profit" if net_after_fixed >= 0 else "Loss",
        delta_color="normal" if net_after_fixed >= 0 else "inverse",
    )
