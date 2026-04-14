"""Daily Overview — rich KPI cards, vibrant charts, section breakdown."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.analytics import (
    today_summary, section_breakdown, compare_averages,
    same_day_last_week, mtd_summary, expense_summary, generate_alerts,
)
from hangout.config import CURRENCY_SYMBOL

SECTION_COLORS = ["#4ade80", "#60a5fa", "#fb923c", "#f472b6", "#facc15", "#22d3ee"]
CHART_FONT = dict(family="Menlo, monospace", color="#94a3b8", size=11)


def _fmt(val):
    if abs(val) >= 100000:
        return f"{CURRENCY_SYMBOL}{val/100000:.2f}L"
    elif abs(val) >= 1000:
        return f"{CURRENCY_SYMBOL}{val/1000:.1f}K"
    return f"{CURRENCY_SYMBOL}{val:,.0f}"


def _kpi_card(icon, label, value, delta=None, accent="#6366f1", glow="99,102,241"):
    """Glassmorphism KPI card with glow effect. Delta shown inline next to label."""
    delta_html = ""
    if delta:
        is_positive = not delta.startswith("-")
        d_color = "#34d399" if is_positive else "#f87171"
        arrow = "▲" if is_positive else "▼"
        bg = "rgba(52,211,153,0.12)" if is_positive else "rgba(248,113,113,0.12)"
        delta_html = (
            f'<span style="display:inline-block;margin-left:8px;padding:2px 8px;'
            f'border-radius:12px;font-size:0.6rem;font-weight:600;vertical-align:middle;'
            f'background:{bg};color:{d_color};letter-spacing:0;">{arrow} {delta}</span>'
        )

    return f"""
    <div style="
        background: linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba({glow},0.08), 0 1px 3px rgba(0,0,0,0.3);
    ">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;
            background:linear-gradient(90deg, {accent}, transparent);"></div>
        <div style="position:absolute;top:-30px;right:-20px;width:80px;height:80px;
            border-radius:50%;background:radial-gradient(circle, rgba({glow},0.08), transparent);"></div>
        <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;
            letter-spacing:0.1em;font-weight:700;">{icon} &nbsp;{label}{delta_html}</div>
        <div style="font-size:2rem;font-weight:800;color:#f1f5f9;margin-top:6px;
            font-family:Menlo,monospace;">{value}</div>
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

    # Alerts — compact inline chips
    alerts = generate_alerts(df, selected_date, expenses)
    if alerts:
        chips = []
        for level, msg in alerts:
            if level == "warning":
                chips.append(
                    f'<span style="display:inline-block;padding:4px 12px;margin:0 6px 6px 0;'
                    f'border-radius:20px;font-size:0.72rem;font-weight:600;'
                    f'background:rgba(251,191,36,0.1);color:#fbbf24;'
                    f'border:1px solid rgba(251,191,36,0.2);">⚠ {msg}</span>'
                )
            else:
                chips.append(
                    f'<span style="display:inline-block;padding:4px 12px;margin:0 6px 6px 0;'
                    f'border-radius:20px;font-size:0.72rem;font-weight:600;'
                    f'background:rgba(52,211,153,0.1);color:#34d399;'
                    f'border:1px solid rgba(52,211,153,0.2);">🎉 {msg}</span>'
                )
        st.markdown(
            f'<div style="margin-bottom:12px;">{"".join(chips)}</div>',
            unsafe_allow_html=True,
        )

    # KPI cards with different accent colors and glows
    comparisons = compare_averages(df, selected_date)
    delta_7d = f"{comparisons[0]['pct_change']:+.1%} vs 7d avg" if comparisons else None
    margin_pct = today["margin_pct"]
    m_accent = "#10b981" if margin_pct >= 0.40 else "#f59e0b" if margin_pct >= 0.35 else "#ef4444"
    m_glow = "16,185,129" if margin_pct >= 0.40 else "245,158,11" if margin_pct >= 0.35 else "239,68,68"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_kpi_card("💰", "Sales", _fmt(today["total_net"]), delta_7d,
                           "#6366f1", "99,102,241"), unsafe_allow_html=True)
    c2.markdown(_kpi_card("📈", "Profit", _fmt(today["total_profit"]), None,
                           "#10b981", "16,185,129"), unsafe_allow_html=True)
    c3.markdown(_kpi_card("📦", "Cost of Goods", _fmt(today["total_cost"]), None,
                           "#8b5cf6", "139,92,246"), unsafe_allow_html=True)
    c4.markdown(_kpi_card("📊", "Margin", f"{margin_pct:.1%}", None,
                           m_accent, m_glow), unsafe_allow_html=True)

    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)

    # Sections + Comparisons
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown("### Sales by Section")
        sections = section_breakdown(df, selected_date)
        active = [s for s in sections if s["net"] > 0]

        if active:
            fig = go.Figure(go.Pie(
                labels=[s["name"] for s in active],
                values=[s["net"] for s in active],
                hole=0.5,
                marker=dict(
                    colors=SECTION_COLORS[:len(active)],
                    line=dict(color="#0f172a", width=2),
                ),
                textinfo="label+percent",
                textposition="outside",
                textfont=dict(size=11, color="#cbd5e1"),
                pull=[0.03] * len(active),
            ))
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), height=320,
                showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                font=CHART_FONT,
                annotations=[dict(
                    text=f"<b>{_fmt(today['total_net'])}</b>",
                    x=0.5, y=0.5, font_size=16, font_color="#f1f5f9",
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)

            # Section table with colored dots
            for i, s in enumerate(active):
                color = SECTION_COLORS[i % len(SECTION_COLORS)]
                cols = st.columns([3, 2, 2, 1])
                cols[0].markdown(
                    f'<span style="color:{color};font-size:1.2rem;">●</span> &nbsp;**{s["name"]}**',
                    unsafe_allow_html=True)
                cols[1].markdown(f"`{_fmt(s['net'])}`")
                cols[2].markdown(f"`{_fmt(s['profit'])}`")
                cols[3].markdown(f"`{s['share_pct']:.0%}`")

    with right:
        st.markdown("### Comparisons")
        for c in comparisons:
            pct = c["pct_change"]
            delta_txt = f"{pct:+.1%} vs today"
            st.markdown(
                _kpi_card("📉" if pct < 0 else "📈", f"{c['window']}-Day Average",
                          _fmt(c["avg_sales"]), delta_txt, "#60a5fa", "96,165,250"),
                unsafe_allow_html=True,
            )
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        lw = same_day_last_week(df, selected_date)
        if lw:
            pct = lw["pct_change"]
            delta_txt = f"{pct:+.1%} vs today"
            st.markdown(
                _kpi_card("📅", f"Last {lw['last_week_date'].strftime('%A')}",
                          _fmt(lw["last_week_sales"]), delta_txt, "#a78bfa", "167,139,250"),
                unsafe_allow_html=True,
            )

    st.divider()

    # MTD
    mtd = mtd_summary(df, selected_date)
    if mtd:
        st.markdown("### Month-to-Date")
        st.caption(f"{mtd['trading_days']} of {mtd['days_in_month']} days  •  {mtd['days_remaining']} remaining")
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(_kpi_card("📆", "MTD Sales", _fmt(mtd["total_sales"]),
                              None, "#60a5fa", "96,165,250"), unsafe_allow_html=True)
        m2.markdown(_kpi_card("💵", "MTD Profit", _fmt(mtd["total_profit"]),
                              None, "#34d399", "52,211,153"), unsafe_allow_html=True)
        m3.markdown(_kpi_card("📊", "Daily Average", _fmt(mtd["daily_avg"]),
                              None, "#fbbf24", "251,191,36"), unsafe_allow_html=True)
        m4.markdown(_kpi_card("🎯", "Projected", _fmt(mtd["projected_monthly"]),
                              None, "#c084fc", "192,132,252"), unsafe_allow_html=True)
        st.progress(mtd["trading_days"] / mtd["days_in_month"])

    st.divider()

    # Expense context
    exp = expense_summary(expenses)
    st.markdown("### Fixed Cost Check")
    net_after = today["total_profit"] - exp["daily_burn"]
    is_profit = net_after >= 0
    net_delta = "Profit" if is_profit else "Loss"
    net_accent = "#34d399" if is_profit else "#f87171"
    net_glow = "52,211,153" if is_profit else "248,113,113"

    e1, e2, e3 = st.columns(3)
    e1.markdown(_kpi_card("🏢", "Monthly Fixed", _fmt(exp["total_monthly"]),
                          None, "#94a3b8", "148,163,184"), unsafe_allow_html=True)
    e2.markdown(_kpi_card("🔥", "Daily Burn", _fmt(exp["daily_burn"]),
                          None, "#fb923c", "251,146,60"), unsafe_allow_html=True)
    e3.markdown(_kpi_card("💎", "Net After Fixed", _fmt(abs(net_after)),
                          net_delta, net_accent, net_glow), unsafe_allow_html=True)
