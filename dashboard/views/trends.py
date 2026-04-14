"""Trends & Analytics — time series, rolling averages, day-of-week patterns."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from hangout.config import CURRENCY_SYMBOL

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=40, l=0, r=0),
    hovermode="x unified",
    legend=dict(orientation="h", y=1.08, font=dict(size=11)),
    xaxis=dict(gridcolor="#f1f5f9", showgrid=False),
    yaxis=dict(gridcolor="#f1f5f9", tickformat=","),
    font=dict(family="Inter, system-ui, sans-serif"),
)


def render(df, expenses):
    st.markdown("# Trends & Analytics")

    trading = df[df["Total Net"] > 0].copy().sort_values("Date")
    if trading.empty:
        st.warning("No data available.")
        return

    period = st.radio("Period", ["7 Days", "30 Days", "90 Days", "All Time"], horizontal=True, label_visibility="collapsed")
    n = {"7 Days": 7, "30 Days": 30, "90 Days": 90, "All Time": None}[period]
    if n:
        trading = trading.tail(n)

    # Sales & Profit
    st.markdown("### Sales & Profit Trend")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trading["Date"], y=trading["Total Net"], name="Sales",
        line=dict(color="#3b82f6", width=2.5),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=trading["Date"], y=trading["Total Profit"], name="Profit",
        line=dict(color="#22c55e", width=2.5),
        fill="tozeroy", fillcolor="rgba(34,197,94,0.08)",
    ))
    if len(trading) >= 7:
        trading["Sales_7d"] = trading["Total Net"].rolling(7).mean()
        fig.add_trace(go.Scatter(
            x=trading["Date"], y=trading["Sales_7d"], name="7-Day Avg",
            line=dict(color="#f59e0b", width=2, dash="dash"),
        ))
    fig.update_layout(**CHART_LAYOUT, height=380)
    st.plotly_chart(fig, use_container_width=True)

    # Margin + Cost split side by side
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### Profit Margin")
        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(
            x=trading["Date"], y=trading["Total Margin %"] * 100, name="Margin %",
            line=dict(color="#ef4444", width=2.5),
            fill="tozeroy", fillcolor="rgba(239,68,68,0.06)",
        ))
        fig_m.add_hline(y=35, line_dash="dash", line_color="#f59e0b",
                         annotation_text="35% Target", annotation_position="top left")
        fig_m.update_layout(**CHART_LAYOUT, height=280, yaxis_title="Margin %")
        st.plotly_chart(fig_m, use_container_width=True)

    with right:
        st.markdown("### Cost vs Profit")
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(x=trading["Date"], y=trading["Total Cost"],
                                name="Cost", marker_color="#8b5cf6"))
        fig_s.add_trace(go.Bar(x=trading["Date"], y=trading["Total Profit"],
                                name="Profit", marker_color="#22c55e"))
        fig_s.update_layout(**CHART_LAYOUT, barmode="stack", height=280)
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

    colors_sales = ["#3b82f6" if d not in ("Friday", "Saturday") else "#2563eb" for d in dow.index]

    fig_dow = go.Figure()
    fig_dow.add_trace(go.Bar(x=dow.index, y=dow["avg_sales"], name="Avg Sales",
                              marker_color=colors_sales))
    fig_dow.add_trace(go.Bar(x=dow.index, y=dow["avg_profit"], name="Avg Profit",
                              marker_color="#22c55e"))
    fig_dow.update_layout(**CHART_LAYOUT, barmode="group", height=300)
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
