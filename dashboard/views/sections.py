"""Section Performance — compare sections over time."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.config import SECTIONS, CURRENCY_SYMBOL

SECTION_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=40, l=0, r=0),
    legend=dict(orientation="h", y=1.08, font=dict(size=11)),
    xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f1f5f9", tickformat=","),
    font=dict(family="Inter, system-ui, sans-serif"),
)


def render(df, expenses):
    st.markdown("# Section Performance")

    trading = df[df["Total Net"] > 0].copy().sort_values("Date")
    if trading.empty:
        st.warning("No data available.")
        return

    section_data = []
    for _, row in trading.iterrows():
        for section in SECTIONS:
            net = row.get(f"{section} Net", 0)
            if net > 0:
                section_data.append({
                    "Date": row["Date"], "Section": section,
                    "Sales": net, "Profit": row.get(f"{section} Profit", 0),
                })

    if not section_data:
        st.warning("No section data available.")
        return

    sec_df = pd.DataFrame(section_data)

    period = st.radio("Period", ["7 Days", "30 Days", "All Time"], horizontal=True, label_visibility="collapsed")
    n = {"7 Days": 7, "30 Days": 30, "All Time": None}[period]
    if n:
        cutoff = trading["Date"].max() - pd.Timedelta(days=n)
        sec_df = sec_df[sec_df["Date"] >= cutoff]

    # Totals
    totals = sec_df.groupby("Section").agg(
        total_sales=("Sales", "sum"), total_profit=("Profit", "sum"),
        avg_daily=("Sales", "mean"),
    ).sort_values("total_sales", ascending=False).reset_index()

    # Scorecards
    st.markdown("### Section Scorecards")
    cols = st.columns(min(len(totals), 4))
    for i, (_, row) in enumerate(totals.iterrows()):
        with cols[i % len(cols)]:
            color = SECTION_COLORS[i % len(SECTION_COLORS)]
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#ffffff,#f8fafc);border:1px solid #e2e8f0;
                border-radius:14px;padding:18px;border-left:4px solid {color};
                box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-bottom:8px;">
                <div style="font-size:0.85rem;font-weight:700;color:#1e293b;">{row['Section']}</div>
                <div style="font-size:1.4rem;font-weight:700;color:{color};margin-top:4px;">
                    {CURRENCY_SYMBOL}{row['total_sales']/100000:.2f}L
                </div>
                <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">
                    Avg/day: {CURRENCY_SYMBOL}{row['avg_daily']/1000:.1f}K &nbsp;•&nbsp;
                    Profit: {CURRENCY_SYMBOL}{row['total_profit']/100000:.2f}L
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # Total bar chart
    st.markdown("### Sales Comparison")
    fig = px.bar(
        totals, x="Section", y="total_sales", color="Section",
        color_discrete_sequence=SECTION_COLORS, text_auto=",.0f",
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(**CHART_LAYOUT, height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Trends side by side
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### Sales Over Time")
        fig_t = px.area(sec_df, x="Date", y="Sales", color="Section",
                         color_discrete_sequence=SECTION_COLORS)
        fig_t.update_layout(**CHART_LAYOUT, height=350)
        st.plotly_chart(fig_t, use_container_width=True)

    with right:
        st.markdown("### Revenue Share")
        daily_totals = sec_df.groupby(["Date", "Section"])["Sales"].sum().reset_index()
        date_totals = daily_totals.groupby("Date")["Sales"].sum().reset_index().rename(columns={"Sales": "DayTotal"})
        daily_totals = daily_totals.merge(date_totals, on="Date")
        daily_totals["Share"] = daily_totals["Sales"] / daily_totals["DayTotal"] * 100
        fig_s = px.area(daily_totals, x="Date", y="Share", color="Section",
                         color_discrete_sequence=SECTION_COLORS, groupnorm="percent")
        fig_s.update_layout(**CHART_LAYOUT, height=350, yaxis_title="Share %")
        st.plotly_chart(fig_s, use_container_width=True)
