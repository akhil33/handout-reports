"""Expenses page — fixed costs, break-even analysis, P&L summary."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.analytics import expense_summary, mtd_summary
from hangout.config import CURRENCY_SYMBOL, DEFAULT_DAYS_IN_MONTH


def _fmt(val):
    if val >= 100000:
        return f"{CURRENCY_SYMBOL}{val/100000:.2f}L"
    elif val >= 1000:
        return f"{CURRENCY_SYMBOL}{val/1000:.1f}K"
    return f"{CURRENCY_SYMBOL}{val:,.0f}"


def render(df, expenses):
    st.header("Expenses & P&L")

    exp = expense_summary(expenses)
    trading = df[df["Total Net"] > 0].copy().sort_values("Date")

    # KPI row
    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Fixed Expenses", _fmt(exp["total_monthly"]))
    c2.metric("Daily Burn Rate", _fmt(exp["daily_burn"]))

    # Break-even: minimum daily sales to cover fixed costs
    if not trading.empty:
        avg_margin = trading["Total Margin %"].mean()
        break_even = exp["daily_burn"] / avg_margin if avg_margin > 0 else 0
        c3.metric("Daily Break-Even Sales", _fmt(break_even), help="Minimum sales to cover fixed costs at average margin")

    st.divider()

    # Expense breakdown
    left, right = st.columns([2, 3])

    with left:
        st.subheader("Fixed Expense Breakdown")
        exp_df = pd.DataFrame([
            {"Expense": k, "Amount": v}
            for k, v in sorted(exp["expenses"].items(), key=lambda x: x[1], reverse=True)
        ])

        fig = px.pie(
            exp_df, values="Amount", names="Expense",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(textinfo="label+percent", textposition="outside")
        fig.update_layout(
            height=400, margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Expense Items")
        for name, amount in sorted(exp["expenses"].items(), key=lambda x: x[1], reverse=True):
            cols = st.columns([3, 2, 2])
            cols[0].write(f"**{name}**")
            cols[1].write(_fmt(amount))
            daily = amount / DEFAULT_DAYS_IN_MONTH
            cols[2].write(f"{_fmt(daily)}/day")

    # Monthly P&L
    if not trading.empty:
        st.divider()
        st.subheader("Monthly Profit & Loss")

        trading["Month"] = trading["Date"].dt.to_period("M").astype(str)
        monthly = trading.groupby("Month").agg(
            revenue=("Total Net", "sum"),
            cogs=("Total Cost", "sum"),
            gross_profit=("Total Profit", "sum"),
            days=("Total Net", "count"),
        ).reset_index()

        monthly["fixed_expenses"] = exp["total_monthly"]
        monthly["net_profit"] = monthly["gross_profit"] - monthly["fixed_expenses"]
        monthly["net_margin"] = monthly["net_profit"] / monthly["revenue"]

        # Stacked bar: COGS + Fixed Expenses + Net Profit = Revenue
        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Bar(
            x=monthly["Month"], y=monthly["cogs"],
            name="Cost of Goods", marker_color="#9333ea",
        ))
        fig_pnl.add_trace(go.Bar(
            x=monthly["Month"], y=monthly["fixed_expenses"],
            name="Fixed Expenses", marker_color="#f59e0b",
        ))
        fig_pnl.add_trace(go.Bar(
            x=monthly["Month"], y=monthly["net_profit"].clip(lower=0),
            name="Net Profit", marker_color="#16a34a",
        ))
        fig_pnl.add_trace(go.Scatter(
            x=monthly["Month"], y=monthly["revenue"],
            name="Revenue", line=dict(color="#3b82f6", width=3),
            mode="lines+markers",
        ))
        fig_pnl.update_layout(
            barmode="stack", height=400,
            margin=dict(t=20, b=40),
            yaxis_tickformat=",",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_pnl, use_container_width=True)

        # Monthly table
        for _, row in monthly.iterrows():
            with st.container():
                cols = st.columns([2, 2, 2, 2, 2, 1])
                cols[0].metric(row["Month"], _fmt(row["revenue"]))
                cols[1].metric("COGS", _fmt(row["cogs"]))
                cols[2].metric("Fixed", _fmt(row["fixed_expenses"]))
                cols[3].metric("Net Profit", _fmt(row["net_profit"]))
                cols[4].metric("Net Margin", f"{row['net_margin']:.1%}")
                cols[5].metric("Days", int(row["days"]))

    # Daily break-even chart
    if not trading.empty:
        st.divider()
        st.subheader("Daily Profit vs Fixed Cost Burn")

        recent = trading.tail(30).copy()
        fig_be = go.Figure()
        fig_be.add_trace(go.Bar(
            x=recent["Date"], y=recent["Total Profit"],
            name="Daily Gross Profit", marker_color="#16a34a",
        ))
        fig_be.add_hline(
            y=exp["daily_burn"], line_dash="dash", line_color="red",
            annotation_text=f"Daily Fixed Cost: {_fmt(exp['daily_burn'])}",
        )
        fig_be.update_layout(
            height=300, margin=dict(t=20, b=40),
            yaxis_tickformat=",",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_be, use_container_width=True)
