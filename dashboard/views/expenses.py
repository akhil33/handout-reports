"""Expenses & P&L — fixed costs, break-even analysis, monthly P&L."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.analytics import expense_summary
from hangout.config import CURRENCY_SYMBOL, DEFAULT_DAYS_IN_MONTH

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=40, l=0, r=0),
    legend=dict(orientation="h", y=1.08, font=dict(size=11, color="#94a3b8")),
    xaxis=dict(showgrid=False, color="#94a3b8"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickformat=",", color="#94a3b8"),
    font=dict(family="Menlo, monospace", color="#cbd5e1"),
)


def _fmt(val):
    if abs(val) >= 100000:
        return f"{CURRENCY_SYMBOL}{val/100000:.2f}L"
    elif abs(val) >= 1000:
        return f"{CURRENCY_SYMBOL}{val/1000:.1f}K"
    return f"{CURRENCY_SYMBOL}{val:,.0f}"


def render(df, expenses):
    st.markdown("# Expenses & P&L")

    exp = expense_summary(expenses)
    trading = df[df["Total Net"] > 0].copy().sort_values("Date")

    # KPI row
    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Fixed Expenses", _fmt(exp["total_monthly"]))
    c2.metric("Daily Burn Rate", _fmt(exp["daily_burn"]))
    if not trading.empty:
        avg_margin = trading["Total Margin %"].mean()
        break_even = exp["daily_burn"] / avg_margin if avg_margin > 0 else 0
        c3.metric("Break-Even Sales/Day", _fmt(break_even),
                   help="Minimum daily sales to cover fixed costs at average margin")

    st.divider()

    # Expense breakdown
    left, right = st.columns([2, 3], gap="large")

    with left:
        st.markdown("### Expense Breakdown")
        exp_df = pd.DataFrame([
            {"Expense": k, "Amount": v}
            for k, v in sorted(exp["expenses"].items(), key=lambda x: x[1], reverse=True)
        ])
        fig = px.pie(exp_df, values="Amount", names="Expense", hole=0.45,
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_traces(textinfo="label+percent", textposition="outside", textfont_size=11)
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=380,
                           showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Expense Details")
        for name, amount in sorted(exp["expenses"].items(), key=lambda x: x[1], reverse=True):
            cols = st.columns([3, 2, 2])
            cols[0].markdown(f"**{name}**")
            cols[1].markdown(f"`{_fmt(amount)}/mo`")
            cols[2].markdown(f"`{_fmt(amount / DEFAULT_DAYS_IN_MONTH)}/day`")

    # Monthly P&L
    if not trading.empty:
        st.divider()
        st.markdown("### Monthly Profit & Loss")

        trading["Month"] = trading["Date"].dt.to_period("M").astype(str)
        monthly = trading.groupby("Month").agg(
            revenue=("Total Net", "sum"), cogs=("Total Cost", "sum"),
            gross_profit=("Total Profit", "sum"), days=("Total Net", "count"),
        ).reset_index()
        monthly["fixed"] = exp["total_monthly"]
        monthly["net_profit"] = monthly["gross_profit"] - monthly["fixed"]
        monthly["net_margin"] = monthly["net_profit"] / monthly["revenue"]

        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Bar(x=monthly["Month"], y=monthly["cogs"],
                                   name="COGS", marker_color="#8b5cf6"))
        fig_pnl.add_trace(go.Bar(x=monthly["Month"], y=monthly["fixed"],
                                   name="Fixed Expenses", marker_color="#f59e0b"))
        fig_pnl.add_trace(go.Bar(x=monthly["Month"], y=monthly["net_profit"].clip(lower=0),
                                   name="Net Profit", marker_color="#22c55e"))
        fig_pnl.add_trace(go.Scatter(x=monthly["Month"], y=monthly["revenue"],
                                       name="Revenue", line=dict(color="#3b82f6", width=3),
                                       mode="lines+markers"))
        fig_pnl.update_layout(**CHART_LAYOUT, barmode="stack", height=400)
        st.plotly_chart(fig_pnl, use_container_width=True)

        # Monthly table
        for _, row in monthly.iterrows():
            cols = st.columns([2, 2, 2, 2, 2, 1])
            cols[0].metric(row["Month"], _fmt(row["revenue"]))
            cols[1].metric("COGS", _fmt(row["cogs"]))
            cols[2].metric("Fixed", _fmt(row["fixed"]))
            cols[3].metric("Net Profit", _fmt(row["net_profit"]))
            cols[4].metric("Net Margin", f"{row['net_margin']:.1%}")
            cols[5].metric("Days", int(row["days"]))

        # Daily break-even chart
        st.divider()
        st.markdown("### Daily Profit vs Fixed Cost Burn")
        st.caption("Green bars above the red line = covering fixed costs that day")

        recent = trading.tail(30).copy()
        fig_be = go.Figure()
        colors = ["#22c55e" if p >= exp["daily_burn"] else "#fca5a5" for p in recent["Total Profit"]]
        fig_be.add_trace(go.Bar(x=recent["Date"], y=recent["Total Profit"],
                                  name="Gross Profit", marker_color=colors))
        fig_be.add_hline(y=exp["daily_burn"], line_dash="dash", line_color="#ef4444", line_width=2,
                          annotation_text=f"Daily Fixed: {_fmt(exp['daily_burn'])}")
        fig_be.update_layout(**CHART_LAYOUT, height=300, showlegend=False)
        st.plotly_chart(fig_be, use_container_width=True)
