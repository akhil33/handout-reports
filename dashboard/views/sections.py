"""Section Performance — vibrant scorecards, rich area/bar charts."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.config import SECTIONS, CURRENCY_SYMBOL

# High-contrast colors that are clearly distinguishable on dark backgrounds
SECTION_COLORS = ["#4ade80", "#60a5fa", "#fb923c", "#f472b6", "#facc15", "#22d3ee"]
SECTION_GLOWS = [
    "74,222,128", "96,165,250", "251,146,60", "244,114,182", "250,204,21", "34,211,238"
]
CHART_FONT = dict(family="Menlo, monospace", color="#94a3b8", size=11)

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=40, l=0, r=0),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="rgba(255,255,255,0.1)",
                    font=dict(color="#f1f5f9", family="Menlo, monospace")),
    legend=dict(orientation="h", y=1.08, font=dict(size=11, color="#94a3b8")),
    xaxis=dict(showgrid=False, color="#64748b", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickformat=",", color="#64748b",
               tickfont=dict(size=10)),
    font=CHART_FONT,
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

    period = st.radio("Period", ["7 Days", "30 Days", "All Time"],
                       horizontal=True, label_visibility="collapsed")
    n = {"7 Days": 7, "30 Days": 30, "All Time": None}[period]
    if n:
        cutoff = trading["Date"].max() - pd.Timedelta(days=n)
        sec_df = sec_df[sec_df["Date"] >= cutoff]

    totals = sec_df.groupby("Section").agg(
        total_sales=("Sales", "sum"), total_profit=("Profit", "sum"),
        avg_daily=("Sales", "mean"),
    ).sort_values("total_sales", ascending=False).reset_index()

    # Glowing scorecards
    st.markdown("### Section Scorecards")
    cols = st.columns(min(len(totals), 4))
    for i, (_, row) in enumerate(totals.iterrows()):
        with cols[i % len(cols)]:
            color = SECTION_COLORS[i % len(SECTION_COLORS)]
            glow = SECTION_GLOWS[i % len(SECTION_GLOWS)]
            share = row["total_sales"] / totals["total_sales"].sum() * 100
            st.markdown(f"""
            <div style="
                background:linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));
                border:1px solid rgba(255,255,255,0.06);
                border-radius:16px;padding:20px;
                border-left:4px solid {color};
                box-shadow:0 4px 20px rgba({glow},0.1), 0 1px 3px rgba(0,0,0,0.3);
                margin-bottom:8px;position:relative;overflow:hidden;
            ">
                <div style="position:absolute;top:-20px;right:-10px;width:60px;height:60px;
                    border-radius:50%;background:radial-gradient(circle,rgba({glow},0.1),transparent);"></div>
                <div style="font-size:0.85rem;font-weight:700;color:#e2e8f0;">{row['Section']}</div>
                <div style="font-size:1.5rem;font-weight:800;color:{color};margin-top:6px;
                    font-family:Menlo,monospace;">
                    {CURRENCY_SYMBOL}{row['total_sales']/100000:.2f}L
                </div>
                <div style="font-size:0.72rem;color:#64748b;margin-top:6px;line-height:1.5;">
                    {CURRENCY_SYMBOL}{row['avg_daily']/1000:.1f}K/day &nbsp;•&nbsp;
                    {share:.0f}% share
                </div>
                <div style="margin-top:8px;height:4px;background:rgba(255,255,255,0.06);border-radius:4px;">
                    <div style="height:4px;width:{min(share*2,100):.0f}%;background:{color};
                        border-radius:4px;"></div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # Bar chart with rounded bars and gradient colors
    st.markdown("### Sales Comparison")
    fig = go.Figure()
    for i, (_, row) in enumerate(totals.iterrows()):
        color = SECTION_COLORS[i % len(SECTION_COLORS)]
        fig.add_trace(go.Bar(
            x=[row["Section"]], y=[row["total_sales"]],
            name=row["Section"],
            marker=dict(color=color, line=dict(width=0), cornerradius=8),
            text=f"₹{row['total_sales']/100000:.1f}L",
            textposition="outside", textfont=dict(size=11, color="#94a3b8"),
            showlegend=False,
        ))
    fig.update_layout(**CHART_LAYOUT, height=350, bargap=0.3)
    st.plotly_chart(fig, use_container_width=True)

    # Trends side by side
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### Sales Over Time")
        fig_t = go.Figure()
        for i, section in enumerate(totals["Section"]):
            s = sec_df[sec_df["Section"] == section].sort_values("Date")
            color = SECTION_COLORS[i % len(SECTION_COLORS)]
            glow = SECTION_GLOWS[i % len(SECTION_GLOWS)]
            fig_t.add_trace(go.Scatter(
                x=s["Date"], y=s["Sales"], name=section,
                line=dict(color=color, width=1, shape="spline"),
                fill="tozeroy",
                fillcolor=f"rgba({glow},0.06)",
                mode="lines",
            ))
        fig_t.update_layout(**CHART_LAYOUT, height=370)
        st.plotly_chart(fig_t, use_container_width=True)

    with right:
        st.markdown("### Revenue Share")
        daily_totals = sec_df.groupby(["Date", "Section"])["Sales"].sum().reset_index()
        date_totals = daily_totals.groupby("Date")["Sales"].sum().reset_index().rename(columns={"Sales": "DayTotal"})
        daily_totals = daily_totals.merge(date_totals, on="Date")
        daily_totals["Share"] = daily_totals["Sales"] / daily_totals["DayTotal"] * 100
        fig_s = px.area(daily_totals, x="Date", y="Share", color="Section",
                         color_discrete_sequence=SECTION_COLORS, groupnorm="percent")
        fig_s.update_layout(**CHART_LAYOUT, height=370, yaxis_title="")
        st.plotly_chart(fig_s, use_container_width=True)
