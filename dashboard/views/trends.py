"""Trends & Analytics — vibrant charts, gradient fills, rich colors."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from hangout.config import CURRENCY_SYMBOL

CHART_FONT = dict(family="Menlo, monospace", color="#94a3b8", size=11)

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=40, l=0, r=0),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="rgba(255,255,255,0.1)",
                    font=dict(color="#f1f5f9", family="Menlo, monospace")),
    legend=dict(orientation="h", y=1.08, font=dict(size=11, color="#94a3b8")),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", showgrid=False, color="#64748b",
               tickfont=dict(size=10)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickformat=",", color="#64748b",
               tickfont=dict(size=10)),
    font=CHART_FONT,
)


def render(df, expenses):
    st.markdown("# Trends & Analytics")

    trading = df[df["Total Net"] > 0].copy().sort_values("Date")
    if trading.empty:
        st.warning("No data available.")
        return

    period = st.radio("Period", ["7 Days", "30 Days", "90 Days", "All Time"],
                       horizontal=True, label_visibility="collapsed")
    n = {"7 Days": 7, "30 Days": 30, "90 Days": 90, "All Time": None}[period]
    if n:
        trading = trading.tail(n)

    # Sales & Profit — gradient area fills
    st.markdown("### Sales & Profit Trend")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trading["Date"], y=trading["Total Net"], name="Sales",
        line=dict(color="#818cf8", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(129,140,248,0.12)",
        mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=trading["Date"], y=trading["Total Profit"], name="Profit",
        line=dict(color="#34d399", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(52,211,153,0.10)",
        mode="lines",
    ))
    if len(trading) >= 7:
        trading["Sales_7d"] = trading["Total Net"].rolling(7).mean()
        fig.add_trace(go.Scatter(
            x=trading["Date"], y=trading["Sales_7d"], name="7-Day Avg",
            line=dict(color="#fbbf24", width=2.5, dash="dot", shape="spline"),
            mode="lines",
        ))
    fig.update_layout(**CHART_LAYOUT, height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Margin + Cost split
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### Profit Margin")
        fig_m = go.Figure()

        # Color-coded margin line — green above 35, red below
        colors = ["#34d399" if m >= 0.35 else "#f87171" for m in trading["Total Margin %"]]
        fig_m.add_trace(go.Scatter(
            x=trading["Date"], y=trading["Total Margin %"] * 100, name="Margin %",
            line=dict(color="#f472b6", width=3, shape="spline"),
            fill="tozeroy", fillcolor="rgba(244,114,182,0.08)",
            mode="lines+markers",
            marker=dict(size=5, color=colors, line=dict(width=0)),
        ))
        fig_m.add_hline(y=35, line_dash="dash", line_color="rgba(251,191,36,0.5)", line_width=2,
                         annotation=dict(text="35% Target", font=dict(color="#fbbf24", size=10)))
        fig_m.update_layout(**CHART_LAYOUT, height=300, yaxis_title="")
        st.plotly_chart(fig_m, use_container_width=True)

    with right:
        st.markdown("### Cost vs Profit")
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=trading["Date"], y=trading["Total Cost"], name="Cost",
            marker=dict(color="#a78bfa", line=dict(width=0),
                        pattern=dict(shape="", fillmode="replace")),
        ))
        fig_s.add_trace(go.Bar(
            x=trading["Date"], y=trading["Total Profit"], name="Profit",
            marker=dict(color="#34d399", line=dict(width=0)),
        ))
        fig_s.update_layout(**CHART_LAYOUT, barmode="stack", height=300, bargap=0.15)
        st.plotly_chart(fig_s, use_container_width=True)

    st.divider()

    # Day-of-week
    st.markdown("### Day-of-Week Patterns")
    st.caption("Which days perform best? Use this to optimize staffing.")

    trading["Weekday"] = trading["Date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = trading.groupby("Weekday").agg(
        avg_sales=("Total Net", "mean"), avg_profit=("Total Profit", "mean"),
    ).reindex(order).dropna()

    # Gradient colors — weekend days get warmer tones
    bar_colors = ["#818cf8", "#818cf8", "#818cf8", "#818cf8",
                  "#c084fc", "#f472b6", "#fb923c"][:len(dow)]

    fig_dow = go.Figure()
    fig_dow.add_trace(go.Bar(
        x=dow.index, y=dow["avg_sales"], name="Avg Sales",
        marker=dict(color=bar_colors, line=dict(width=0),
                    cornerradius=6),
        text=[f"₹{v/1000:.0f}K" for v in dow["avg_sales"]],
        textposition="outside", textfont=dict(size=10, color="#94a3b8"),
    ))
    fig_dow.add_trace(go.Bar(
        x=dow.index, y=dow["avg_profit"], name="Avg Profit",
        marker=dict(color=["rgba(52,211,153,0.7)"] * len(dow),
                    line=dict(width=0), cornerradius=6),
    ))
    fig_dow.update_layout(**CHART_LAYOUT, barmode="group", height=320, bargap=0.2, bargroupgap=0.05)
    st.plotly_chart(fig_dow, use_container_width=True)

    st.divider()

    # Monthly summary
    st.markdown("### Monthly Summary")
    trading["Month"] = trading["Date"].dt.to_period("M").astype(str)
    monthly = trading.groupby("Month").agg(
        total_sales=("Total Net", "sum"), total_profit=("Total Profit", "sum"),
        avg_daily=("Total Net", "mean"), trading_days=("Total Net", "count"),
        avg_margin=("Total Margin %", "mean"),
    ).reset_index()

    for _, row in monthly.iterrows():
        cols = st.columns([2, 2, 2, 1, 1])
        cols[0].metric(row["Month"], f"{CURRENCY_SYMBOL}{row['total_sales']/100000:.1f}L")
        cols[1].metric("Profit", f"{CURRENCY_SYMBOL}{row['total_profit']/100000:.1f}L")
        cols[2].metric("Daily Avg", f"{CURRENCY_SYMBOL}{row['avg_daily']/1000:.0f}K")
        cols[3].metric("Days", int(row["trading_days"]))
        cols[4].metric("Margin", f"{row['avg_margin']:.1%}")
