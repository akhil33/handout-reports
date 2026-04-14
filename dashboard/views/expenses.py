"""Expenses & P&L — rich charts, gradient bars, break-even analysis."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hangout.analytics import expense_summary
from hangout.config import CURRENCY_SYMBOL, DEFAULT_DAYS_IN_MONTH

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

# Rich expense pie colors
PIE_COLORS = [
    "#6366f1", "#818cf8", "#a78bfa", "#c084fc",
    "#06b6d4", "#22d3ee", "#34d399", "#10b981",
    "#f59e0b", "#fbbf24", "#f472b6", "#ec4899",
    "#f97316", "#fb923c", "#94a3b8", "#64748b",
]


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
        fig = go.Figure(go.Pie(
            labels=exp_df["Expense"], values=exp_df["Amount"],
            hole=0.5,
            marker=dict(colors=PIE_COLORS[:len(exp_df)],
                        line=dict(color="#0f172a", width=2)),
            textinfo="label+percent", textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
            pull=[0.03 if i == 0 else 0 for i in range(len(exp_df))],
        ))
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10), height=400,
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)", font=CHART_FONT,
            annotations=[dict(
                text=f"<b>{_fmt(exp['total_monthly'])}</b><br><span style='font-size:10px'>/ month</span>",
                x=0.5, y=0.5, font_size=14, font_color="#f1f5f9", showarrow=False,
            )],
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Expense Details")
        for i, (name, amount) in enumerate(sorted(exp["expenses"].items(), key=lambda x: x[1], reverse=True)):
            color = PIE_COLORS[i % len(PIE_COLORS)]
            pct = amount / exp["total_monthly"] * 100
            cols = st.columns([3, 2, 2])
            cols[0].markdown(
                f'<span style="color:{color};">●</span> &nbsp;**{name}**',
                unsafe_allow_html=True)
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
        fig_pnl.add_trace(go.Bar(
            x=monthly["Month"], y=monthly["cogs"], name="COGS",
            marker=dict(color="#a78bfa", line=dict(width=0), cornerradius=4),
        ))
        fig_pnl.add_trace(go.Bar(
            x=monthly["Month"], y=monthly["fixed"], name="Fixed Expenses",
            marker=dict(color="#fbbf24", line=dict(width=0), cornerradius=4),
        ))
        fig_pnl.add_trace(go.Bar(
            x=monthly["Month"], y=monthly["net_profit"].clip(lower=0), name="Net Profit",
            marker=dict(color="#34d399", line=dict(width=0), cornerradius=4),
        ))
        fig_pnl.add_trace(go.Scatter(
            x=monthly["Month"], y=monthly["revenue"], name="Revenue",
            line=dict(color="#818cf8", width=3, shape="spline"),
            mode="lines+markers",
            marker=dict(size=8, color="#818cf8", line=dict(color="#0f172a", width=2)),
        ))
        fig_pnl.update_layout(**CHART_LAYOUT, barmode="stack", height=420, bargap=0.25)
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

        # Daily break-even
        st.divider()
        st.markdown("### Daily Profit vs Fixed Cost Burn")
        st.caption("Green = covering fixed costs, Red = below break-even")

        recent = trading.tail(30).copy()
        colors = [
            "#34d399" if p >= exp["daily_burn"] else "#f87171"
            for p in recent["Total Profit"]
        ]
        fig_be = go.Figure()
        fig_be.add_trace(go.Bar(
            x=recent["Date"], y=recent["Total Profit"], name="Gross Profit",
            marker=dict(color=colors, line=dict(width=0), cornerradius=6),
        ))
        fig_be.add_hline(
            y=exp["daily_burn"], line_dash="dash", line_color="rgba(251,191,36,0.6)", line_width=2,
            annotation=dict(text=f"Daily Fixed: {_fmt(exp['daily_burn'])}",
                           font=dict(color="#fbbf24", size=10)),
        )
        fig_be.update_layout(**CHART_LAYOUT, height=320, showlegend=False, bargap=0.15)
        st.plotly_chart(fig_be, use_container_width=True)
