"""Trends & Analytics page — time series charts, rolling averages, patterns."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.config import CURRENCY_SYMBOL


def render(df, expenses):
    st.header("Trends & Analytics")

    trading = df[df["Total Net"] > 0].copy()
    trading = trading.sort_values("Date")

    if trading.empty:
        st.warning("No data available.")
        return

    # Time range selector
    range_opt = st.radio(
        "Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
        horizontal=True,
    )
    range_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90, "All Time": None}
    n = range_map[range_opt]
    if n:
        trading = trading.tail(n)

    # Sales & Profit trend
    st.subheader("Sales & Profit")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trading["Date"], y=trading["Total Net"],
        name="Sales", line=dict(color="#3b82f6", width=2),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=trading["Date"], y=trading["Total Profit"],
        name="Profit", line=dict(color="#16a34a", width=2),
        fill="tozeroy", fillcolor="rgba(22,163,106,0.1)",
    ))

    # 7-day rolling average
    if len(trading) >= 7:
        trading["Sales_7d"] = trading["Total Net"].rolling(7).mean()
        fig.add_trace(go.Scatter(
            x=trading["Date"], y=trading["Sales_7d"],
            name="7-Day Avg", line=dict(color="#f59e0b", width=2, dash="dash"),
        ))

    fig.update_layout(
        height=400,
        margin=dict(t=20, b=40),
        hovermode="x unified",
        yaxis_title=f"Amount ({CURRENCY_SYMBOL})",
        yaxis_tickformat=",",
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Margin trend
    left, right = st.columns(2)

    with left:
        st.subheader("Profit Margin %")
        fig_margin = go.Figure()
        fig_margin.add_trace(go.Scatter(
            x=trading["Date"], y=trading["Total Margin %"] * 100,
            name="Margin %", line=dict(color="#dc2626", width=2),
            fill="tozeroy", fillcolor="rgba(220,38,38,0.1)",
        ))
        # Threshold line
        fig_margin.add_hline(
            y=35, line_dash="dash", line_color="orange",
            annotation_text="35% Target",
        )
        fig_margin.update_layout(
            height=300, margin=dict(t=20, b=40),
            yaxis_title="Margin %",
        )
        st.plotly_chart(fig_margin, use_container_width=True)

    with right:
        st.subheader("Cost vs Profit Split")
        fig_stack = go.Figure()
        fig_stack.add_trace(go.Bar(
            x=trading["Date"], y=trading["Total Cost"],
            name="Cost", marker_color="#9333ea",
        ))
        fig_stack.add_trace(go.Bar(
            x=trading["Date"], y=trading["Total Profit"],
            name="Profit", marker_color="#16a34a",
        ))
        fig_stack.update_layout(
            barmode="stack", height=300, margin=dict(t=20, b=40),
            yaxis_tickformat=",",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

    # Day-of-week analysis
    st.divider()
    st.subheader("Day-of-Week Patterns")

    trading["Weekday"] = trading["Date"].dt.day_name()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = trading.groupby("Weekday").agg(
        avg_sales=("Total Net", "mean"),
        avg_profit=("Total Profit", "mean"),
        count=("Total Net", "count"),
    ).reindex(weekday_order).dropna()

    fig_dow = go.Figure()
    fig_dow.add_trace(go.Bar(
        x=dow.index, y=dow["avg_sales"],
        name="Avg Sales", marker_color="#3b82f6",
    ))
    fig_dow.add_trace(go.Bar(
        x=dow.index, y=dow["avg_profit"],
        name="Avg Profit", marker_color="#16a34a",
    ))
    fig_dow.update_layout(
        height=300, margin=dict(t=20, b=40),
        barmode="group",
        yaxis_tickformat=",",
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_dow, use_container_width=True)

    # Monthly summary
    st.divider()
    st.subheader("Monthly Summary")

    trading["Month"] = trading["Date"].dt.to_period("M").astype(str)
    monthly = trading.groupby("Month").agg(
        total_sales=("Total Net", "sum"),
        total_profit=("Total Profit", "sum"),
        avg_daily=("Total Net", "mean"),
        trading_days=("Total Net", "count"),
        avg_margin=("Total Margin %", "mean"),
    ).reset_index()

    for _, row in monthly.iterrows():
        with st.container():
            cols = st.columns([2, 2, 2, 1, 1])
            cols[0].metric(row["Month"], f"{CURRENCY_SYMBOL}{row['total_sales']/100000:.1f}L")
            cols[1].metric("Profit", f"{CURRENCY_SYMBOL}{row['total_profit']/100000:.1f}L")
            cols[2].metric("Daily Avg", f"{CURRENCY_SYMBOL}{row['avg_daily']/1000:.0f}K")
            cols[3].metric("Days", int(row["trading_days"]))
            cols[4].metric("Margin", f"{row['avg_margin']:.1%}")
