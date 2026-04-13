"""Section Performance page — compare sections over time."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.config import SECTIONS, CURRENCY_SYMBOL


def render(df, expenses):
    st.header("Section Performance")

    trading = df[df["Total Net"] > 0].copy().sort_values("Date")
    if trading.empty:
        st.warning("No data available.")
        return

    # Build section time series
    section_data = []
    for _, row in trading.iterrows():
        for section in SECTIONS:
            net = row.get(f"{section} Net", 0)
            if net > 0:
                section_data.append({
                    "Date": row["Date"],
                    "Section": section,
                    "Sales": net,
                    "Profit": row.get(f"{section} Profit", 0),
                })

    if not section_data:
        st.warning("No section data available.")
        return

    sec_df = pd.DataFrame(section_data)

    # Time range
    range_opt = st.radio("Period", ["Last 7 Days", "Last 30 Days", "All Time"], horizontal=True)
    range_map = {"Last 7 Days": 7, "Last 30 Days": 30, "All Time": None}
    n = range_map[range_opt]
    if n:
        cutoff = trading["Date"].max() - pd.Timedelta(days=n)
        sec_df = sec_df[sec_df["Date"] >= cutoff]

    # Section comparison — totals
    st.subheader("Total Sales by Section")
    totals = sec_df.groupby("Section").agg(
        total_sales=("Sales", "sum"),
        total_profit=("Profit", "sum"),
        avg_daily=("Sales", "mean"),
    ).sort_values("total_sales", ascending=False).reset_index()

    fig = px.bar(
        totals, x="Section", y="total_sales",
        color="Section", color_discrete_sequence=px.colors.qualitative.Set2,
        text_auto=",.0f",
    )
    fig.update_layout(
        height=350, margin=dict(t=20, b=40),
        showlegend=False, yaxis_tickformat=",",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Section trends over time
    st.subheader("Section Sales Over Time")
    fig_trend = px.area(
        sec_df, x="Date", y="Sales", color="Section",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_trend.update_layout(
        height=400, margin=dict(t=20, b=40),
        yaxis_tickformat=",",
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Share over time (stacked percentage)
    st.subheader("Revenue Share Over Time")
    daily_totals = sec_df.groupby(["Date", "Section"])["Sales"].sum().reset_index()
    date_totals = daily_totals.groupby("Date")["Sales"].sum().reset_index().rename(columns={"Sales": "DayTotal"})
    daily_totals = daily_totals.merge(date_totals, on="Date")
    daily_totals["Share"] = daily_totals["Sales"] / daily_totals["DayTotal"] * 100

    fig_share = px.area(
        daily_totals, x="Date", y="Share", color="Section",
        color_discrete_sequence=px.colors.qualitative.Set2,
        groupnorm="percent",
    )
    fig_share.update_layout(
        height=350, margin=dict(t=20, b=40),
        yaxis_title="Share %",
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig_share, use_container_width=True)

    # Section scorecards
    st.divider()
    st.subheader("Section Scorecards")
    cols = st.columns(min(len(totals), 3))
    for i, (_, row) in enumerate(totals.iterrows()):
        with cols[i % len(cols)]:
            st.metric(row["Section"], f"{CURRENCY_SYMBOL}{row['total_sales']/100000:.2f}L total")
            st.caption(f"Avg/day: {CURRENCY_SYMBOL}{row['avg_daily']/1000:.1f}K | Profit: {CURRENCY_SYMBOL}{row['total_profit']/100000:.2f}L")
