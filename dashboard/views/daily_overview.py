"""Daily Overview — KPIs, section breakdown, comparisons, MTD."""
import streamlit as st
import plotly.express as px
import pandas as pd
from hangout.analytics import (
    today_summary, section_breakdown, compare_averages,
    same_day_last_week, mtd_summary, expense_summary, generate_alerts,
)
from hangout.config import CURRENCY_SYMBOL

SECTION_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]


def _fmt(val):
    if abs(val) >= 100000:
        return f"{CURRENCY_SYMBOL}{val/100000:.2f}L"
    elif abs(val) >= 1000:
        return f"{CURRENCY_SYMBOL}{val/1000:.1f}K"
    return f"{CURRENCY_SYMBOL}{val:,.0f}"


def _kpi_card(icon, label, value, delta=None, color="#3b82f6"):
    delta_html = ""
    if delta:
        d_color = "#22c55e" if not delta.startswith("-") else "#ef4444"
        arrow = "▲" if not delta.startswith("-") else "▼"
        delta_html = f'<div style="font-size:0.78rem;color:{d_color};margin-top:4px;">{arrow} {delta}</div>'
    return f"""
    <div style="background:#1e293b;border:1px solid rgba(255,255,255,0.06);
        border-radius:14px;padding:20px;border-top:3px solid {color};
        box-shadow:0 2px 8px rgba(0,0,0,0.2);">
        <div style="font-size:0.7rem;color:#94a3b8;text-transform:uppercase;
            letter-spacing:0.08em;font-weight:600;">{icon} {label}</div>
        <div style="font-size:1.8rem;font-weight:700;color:#f1f5f9;margin-top:6px;">{value}</div>
        {delta_html}
    </div>"""


def render(df, expenses):
    available_dates = df[df["Total Net"] > 0]["Date"].dt.date.tolist()
    if not available_dates:
        st.warning("No sales data available. Click **Sync Today** in the sidebar.")
        return

    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown("# Daily Overview")
    with h2:
        selected_date = st.date_input(
            "Date", value=available_dates[0],
            min_value=available_dates[-1], max_value=available_dates[0],
            label_visibility="collapsed",
        )

    today = today_summary(df, selected_date)
    if today is None:
        st.info(f"No sales recorded on {selected_date.strftime('%B %d, %Y')}.")
        return

    # Alerts
    for level, msg in generate_alerts(df, selected_date, expenses):
        (st.warning if level == "warning" else st.success)(msg, icon="⚠️" if level == "warning" else "🎉")

    # KPI cards
    comparisons = compare_averages(df, selected_date)
    delta_7d = f"{comparisons[0]['pct_change']:+.1%} vs 7d avg" if comparisons else None
    margin_color = "#22c55e" if today["margin_pct"] >= 0.40 else "#f59e0b" if today["margin_pct"] >= 0.35 else "#ef4444"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_kpi_card("💰", "Sales", _fmt(today["total_net"]), delta_7d, "#3b82f6"), unsafe_allow_html=True)
    c2.markdown(_kpi_card("📈", "Profit", _fmt(today["total_profit"]), None, "#22c55e"), unsafe_allow_html=True)
    c3.markdown(_kpi_card("📦", "Cost of Goods", _fmt(today["total_cost"]), None, "#8b5cf6"), unsafe_allow_html=True)
    c4.markdown(_kpi_card("📊", "Margin", f"{today['margin_pct']:.1%}", None, margin_color), unsafe_allow_html=True)

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # Sections + Comparisons
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown("### Sales by Section")
        sections = section_breakdown(df, selected_date)
        active = [s for s in sections if s["net"] > 0]

        if active:
            fig = px.pie(
                pd.DataFrame(active), values="net", names="name", hole=0.45,
                color_discrete_sequence=SECTION_COLORS,
            )
            fig.update_traces(textinfo="label+percent", textposition="outside",
                              textfont_size=12, pull=[0.02]*len(active))
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300,
                              showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              font=dict(family="Menlo, monospace", color="#cbd5e1"))
            st.plotly_chart(fig, use_container_width=True)

            for s in active:
                cols = st.columns([3, 2, 2, 1])
                cols[0].markdown(f"**{s['name']}**")
                cols[1].markdown(f"`{_fmt(s['net'])}`")
                cols[2].markdown(f"`{_fmt(s['profit'])}`")
                cols[3].markdown(f"`{s['share_pct']:.0%}`")

    with right:
        st.markdown("### Comparisons")
        for c in comparisons:
            st.metric(f"{c['window']}-Day Average", _fmt(c["avg_sales"]), f"{c['pct_change']:+.1%}")
        lw = same_day_last_week(df, selected_date)
        if lw:
            st.metric(f"Last {lw['last_week_date'].strftime('%A')}", _fmt(lw["last_week_sales"]),
                       f"{lw['pct_change']:+.1%}")

    st.divider()

    # MTD
    mtd = mtd_summary(df, selected_date)
    if mtd:
        st.markdown("### Month-to-Date")
        st.caption(f"{mtd['trading_days']} of {mtd['days_in_month']} days  •  {mtd['days_remaining']} remaining")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("MTD Sales", _fmt(mtd["total_sales"]))
        m2.metric("MTD Profit", _fmt(mtd["total_profit"]))
        m3.metric("Daily Average", _fmt(mtd["daily_avg"]))
        m4.metric("Projected", _fmt(mtd["projected_monthly"]))
        st.progress(mtd["trading_days"] / mtd["days_in_month"])

    st.divider()

    # Expense context
    exp = expense_summary(expenses)
    st.markdown("### Fixed Cost Check")
    e1, e2, e3 = st.columns(3)
    e1.metric("Monthly Fixed", _fmt(exp["total_monthly"]))
    e2.metric("Daily Burn", _fmt(exp["daily_burn"]))
    net_after = today["total_profit"] - exp["daily_burn"]
    e3.metric("Net After Fixed", _fmt(abs(net_after)),
              "Profit" if net_after >= 0 else "Loss",
              delta_color="normal" if net_after >= 0 else "inverse")
