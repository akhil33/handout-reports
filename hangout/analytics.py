import pandas as pd
from hangout.config import (
    SECTIONS, ROLLING_WINDOWS, MIN_PROFIT_MARGIN,
    LOW_SALES_PERCENTILE, HIGH_SALES_PERCENTILE, DEFAULT_DAYS_IN_MONTH,
)
from hangout.data import (
    get_sales_for_date, get_recent_sales, get_mtd_sales, load_expenses,
)


def today_summary(df, date):
    """Return today's top-level numbers."""
    row = get_sales_for_date(df, date)
    if row is None:
        return None
    return {
        "date": pd.Timestamp(date),
        "total_net": row["Total Net"],
        "total_cost": row["Total Cost"],
        "total_profit": row["Total Profit"],
        "margin_pct": row["Total Margin %"],
    }


def section_breakdown(df, date):
    """Return per-section sales, cost, profit for a given date."""
    row = get_sales_for_date(df, date)
    if row is None:
        return []
    sections = []
    total_net = row["Total Net"]
    for s in SECTIONS:
        net = row.get(f"{s} Net", 0)
        cost = row.get(f"{s} Cost", 0)
        profit = row.get(f"{s} Profit", 0)
        share = net / total_net if total_net > 0 else 0
        sections.append({
            "name": s,
            "net": net,
            "cost": cost,
            "profit": profit,
            "share_pct": share,
        })
    # Sort by net sales descending
    sections.sort(key=lambda x: x["net"], reverse=True)
    return sections


def compare_averages(df, date, windows=None):
    """Compare today's sales against rolling averages."""
    windows = windows or ROLLING_WINDOWS
    today = get_sales_for_date(df, date)
    if today is None:
        return []

    today_net = today["Total Net"]
    comparisons = []
    for w in windows:
        recent = get_recent_sales(df, date, w + 1)  # +1 to include today
        # Exclude today for the average
        past = recent[recent["Date"].dt.normalize() < pd.Timestamp(date).normalize()]
        if past.empty:
            continue
        avg_net = past["Total Net"].mean()
        avg_profit = past["Total Profit"].mean()
        avg_margin = past["Total Margin %"].mean()
        pct_change = (today_net - avg_net) / avg_net if avg_net > 0 else 0
        comparisons.append({
            "window": w,
            "avg_sales": avg_net,
            "avg_profit": avg_profit,
            "avg_margin": avg_margin,
            "pct_change": pct_change,
        })
    return comparisons


def same_day_last_week(df, date):
    """Compare with the same weekday last week."""
    date = pd.Timestamp(date).normalize()
    last_week = date - pd.Timedelta(days=7)
    today_row = get_sales_for_date(df, date)
    last_week_row = get_sales_for_date(df, last_week)
    if today_row is None or last_week_row is None:
        return None
    today_net = today_row["Total Net"]
    lw_net = last_week_row["Total Net"]
    return {
        "last_week_date": last_week,
        "last_week_sales": lw_net,
        "last_week_profit": last_week_row["Total Profit"],
        "pct_change": (today_net - lw_net) / lw_net if lw_net > 0 else 0,
    }


def mtd_summary(df, date):
    """Month-to-date summary."""
    date = pd.Timestamp(date).normalize()
    mtd = get_mtd_sales(df, date)
    if mtd.empty:
        return None
    days_in_month = date.days_in_month
    trading_days = len(mtd)
    total_sales = mtd["Total Net"].sum()
    total_profit = mtd["Total Profit"].sum()
    total_cost = mtd["Total Cost"].sum()
    daily_avg = total_sales / trading_days if trading_days > 0 else 0
    best_day = mtd.loc[mtd["Total Net"].idxmax()]
    worst_day = mtd.loc[mtd["Total Net"].idxmin()]
    return {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "total_cost": total_cost,
        "trading_days": trading_days,
        "days_in_month": days_in_month,
        "days_remaining": days_in_month - date.day,
        "daily_avg": daily_avg,
        "projected_monthly": daily_avg * days_in_month,
        "avg_margin": (total_profit / total_sales) if total_sales > 0 else 0,
        "best_day_date": best_day["Date"],
        "best_day_sales": best_day["Total Net"],
        "worst_day_date": worst_day["Date"],
        "worst_day_sales": worst_day["Total Net"],
    }


def expense_summary(expenses=None):
    """Calculate expense breakdown and daily burn rate."""
    if expenses is None:
        expenses = load_expenses()
    total_monthly = sum(expenses.values())
    daily_burn = total_monthly / DEFAULT_DAYS_IN_MONTH
    return {
        "expenses": expenses,
        "total_monthly": total_monthly,
        "daily_burn": daily_burn,
    }


def generate_alerts(df, date, expenses=None):
    """Generate alert messages based on thresholds."""
    alerts = []
    today = get_sales_for_date(df, date)
    if today is None:
        alerts.append(("warning", "No sales data for today"))
        return alerts

    # Margin alert
    margin = today["Total Margin %"]
    if margin < MIN_PROFIT_MARGIN:
        alerts.append((
            "warning",
            f"Profit margin is {margin:.1%} — below {MIN_PROFIT_MARGIN:.0%} threshold"
        ))

    # Compare to recent days
    recent = get_recent_sales(df, date, 31)
    past = recent[recent["Date"].dt.normalize() < pd.Timestamp(date).normalize()]
    if len(past) >= 7:
        today_net = today["Total Net"]
        low_threshold = past["Total Net"].quantile(LOW_SALES_PERCENTILE)
        high_threshold = past["Total Net"].quantile(HIGH_SALES_PERCENTILE)
        if today_net < low_threshold:
            alerts.append((
                "warning",
                f"Sales ₹{today_net:,.0f} — unusually low (bottom 20% of last 30 days)"
            ))
        elif today_net > high_threshold:
            alerts.append((
                "success",
                f"Sales ₹{today_net:,.0f} — exceptional day! (top 10% of last 30 days)"
            ))

    # Break-even check
    exp = expense_summary(expenses)
    if today["Total Profit"] < exp["daily_burn"]:
        shortfall = exp["daily_burn"] - today["Total Profit"]
        alerts.append((
            "warning",
            f"Profit ₹{today['Total Profit']:,.0f} is below daily fixed cost ₹{exp['daily_burn']:,.0f} (shortfall: ₹{shortfall:,.0f})"
        ))

    return alerts


def full_report_data(df, date, expenses=None):
    """Assemble all analytics for the daily report."""
    return {
        "today": today_summary(df, date),
        "sections": section_breakdown(df, date),
        "comparisons": compare_averages(df, date),
        "last_week": same_day_last_week(df, date),
        "mtd": mtd_summary(df, date),
        "expenses": expense_summary(expenses),
        "alerts": generate_alerts(df, date, expenses),
    }
