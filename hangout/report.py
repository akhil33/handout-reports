from hangout.config import BUSINESS_NAME, CURRENCY_SYMBOL


def _fmt(amount):
    """Format amount in Indian numbering (lakhs/thousands)."""
    if amount >= 100000:
        return f"{CURRENCY_SYMBOL}{amount / 100000:.2f}L"
    elif amount >= 1000:
        return f"{CURRENCY_SYMBOL}{amount / 1000:.1f}K"
    else:
        return f"{CURRENCY_SYMBOL}{amount:,.0f}"


def _pct(value):
    """Format percentage."""
    return f"{value:.1%}"


def _change_badge(pct_change):
    """Return an HTML badge for positive/negative change."""
    if pct_change > 0:
        color = "#16a34a"
        arrow = "&#9650;"  # ▲
        text = f"+{pct_change:.1%}"
    elif pct_change < 0:
        color = "#dc2626"
        arrow = "&#9660;"  # ▼
        text = f"{pct_change:.1%}"
    else:
        color = "#6b7280"
        arrow = "&#8212;"  # —
        text = "0%"
    return f'<span style="color:{color};font-weight:600;">{arrow} {text}</span>'


def _alert_html(alerts):
    """Render alerts as styled boxes."""
    if not alerts:
        return ""
    html = '<div style="margin-bottom:20px;">'
    for level, msg in alerts:
        if level == "warning":
            bg, border, icon = "#fef3c7", "#f59e0b", "&#9888;"  # ⚠
        else:
            bg, border, icon = "#dcfce7", "#16a34a", "&#10003;"  # ✓
        html += f'''
        <div style="background:{bg};border-left:4px solid {border};padding:10px 14px;
                     margin-bottom:8px;border-radius:4px;font-size:14px;">
            {icon} {msg}
        </div>'''
    html += "</div>"
    return html


def _section_rows(sections):
    """Render section breakdown as table rows."""
    rows = ""
    for s in sections:
        bar_width = max(int(s["share_pct"] * 100), 2)
        rows += f'''
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;font-weight:500;">{s["name"]}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;">{_fmt(s["net"])}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;">{_fmt(s["profit"])}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;">{_pct(s["share_pct"])}</td>
            <td style="padding:8px 4px;border-bottom:1px solid #e5e7eb;width:100px;">
                <div style="background:#dbeafe;border-radius:4px;height:16px;width:100%;">
                    <div style="background:#3b82f6;border-radius:4px;height:16px;width:{bar_width}%;"></div>
                </div>
            </td>
        </tr>'''
    return rows


def build_html_report(data):
    """Build the full HTML email from analytics data."""
    today = data["today"]
    if today is None:
        return f"<html><body><h2>{BUSINESS_NAME}</h2><p>No sales data available for this date.</p></body></html>"

    date_str = today["date"].strftime("%A, %B %d, %Y")
    sections = data["sections"]
    comparisons = data["comparisons"]
    last_week = data["last_week"]
    mtd = data["mtd"]
    expenses = data["expenses"]
    alerts = data["alerts"]

    # Build comparison cards
    comp_html = ""
    for c in comparisons:
        comp_html += f'''
        <td style="padding:12px;text-align:center;width:33%;">
            <div style="font-size:12px;color:#6b7280;text-transform:uppercase;">{c["window"]}-Day Avg</div>
            <div style="font-size:18px;font-weight:700;margin:4px 0;">{_fmt(c["avg_sales"])}</div>
            <div>{_change_badge(c["pct_change"])}</div>
        </td>'''
    if last_week:
        comp_html += f'''
        <td style="padding:12px;text-align:center;width:33%;">
            <div style="font-size:12px;color:#6b7280;text-transform:uppercase;">Last {last_week["last_week_date"].strftime("%a")}</div>
            <div style="font-size:18px;font-weight:700;margin:4px 0;">{_fmt(last_week["last_week_sales"])}</div>
            <div>{_change_badge(last_week["pct_change"])}</div>
        </td>'''

    # MTD section
    mtd_html = ""
    if mtd:
        mtd_html = f'''
        <div style="background:#f8fafc;border-radius:8px;padding:16px;margin-bottom:20px;">
            <h3 style="margin:0 0 12px;color:#1e293b;font-size:16px;">Month-to-Date ({mtd["trading_days"]} of {mtd["days_in_month"]} days)</h3>
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding:8px;text-align:center;">
                        <div style="font-size:11px;color:#6b7280;">MTD SALES</div>
                        <div style="font-size:18px;font-weight:700;">{_fmt(mtd["total_sales"])}</div>
                    </td>
                    <td style="padding:8px;text-align:center;">
                        <div style="font-size:11px;color:#6b7280;">MTD PROFIT</div>
                        <div style="font-size:18px;font-weight:700;">{_fmt(mtd["total_profit"])}</div>
                    </td>
                    <td style="padding:8px;text-align:center;">
                        <div style="font-size:11px;color:#6b7280;">DAILY AVG</div>
                        <div style="font-size:18px;font-weight:700;">{_fmt(mtd["daily_avg"])}</div>
                    </td>
                    <td style="padding:8px;text-align:center;">
                        <div style="font-size:11px;color:#6b7280;">PROJECTED</div>
                        <div style="font-size:18px;font-weight:700;">{_fmt(mtd["projected_monthly"])}</div>
                    </td>
                </tr>
            </table>
            <div style="font-size:12px;color:#6b7280;margin-top:8px;">
                Best: {mtd["best_day_date"].strftime("%b %d")} ({_fmt(mtd["best_day_sales"])})
                &nbsp;|&nbsp;
                Worst: {mtd["worst_day_date"].strftime("%b %d")} ({_fmt(mtd["worst_day_sales"])})
                &nbsp;|&nbsp;
                {mtd["days_remaining"]} days remaining
            </div>
        </div>'''

    # Expense context
    exp_html = f'''
    <div style="background:#fefce8;border-radius:8px;padding:14px;margin-bottom:20px;">
        <div style="font-size:12px;color:#854d0e;font-weight:600;">FIXED EXPENSES</div>
        <div style="font-size:14px;margin-top:4px;">
            Monthly: {_fmt(expenses["total_monthly"])}
            &nbsp;|&nbsp;
            Daily burn: {_fmt(expenses["daily_burn"])}
            &nbsp;|&nbsp;
            Today's net profit after fixed: <strong>{_fmt(today["total_profit"] - expenses["daily_burn"])}</strong>
        </div>
    </div>'''

    # Margin color
    margin_color = "#16a34a" if today["margin_pct"] >= 0.40 else "#f59e0b" if today["margin_pct"] >= 0.35 else "#dc2626"

    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#ffffff;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e293b,#334155);padding:24px;text-align:center;">
        <h1 style="margin:0;color:#ffffff;font-size:22px;letter-spacing:1px;">{BUSINESS_NAME}</h1>
        <div style="color:#94a3b8;font-size:13px;margin-top:4px;">Daily Business Report</div>
        <div style="color:#e2e8f0;font-size:14px;margin-top:8px;font-weight:500;">{date_str}</div>
    </div>

    <div style="padding:20px;">

        <!-- Alerts -->
        {_alert_html(alerts)}

        <!-- Today's Numbers -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
            <tr>
                <td style="padding:12px;text-align:center;background:#f0fdf4;border-radius:8px 0 0 8px;">
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Sales</div>
                    <div style="font-size:22px;font-weight:700;color:#1e293b;">{_fmt(today["total_net"])}</div>
                </td>
                <td style="padding:12px;text-align:center;background:#f0f9ff;">
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Profit</div>
                    <div style="font-size:22px;font-weight:700;color:#1e293b;">{_fmt(today["total_profit"])}</div>
                </td>
                <td style="padding:12px;text-align:center;background:#fefce8;">
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Cost</div>
                    <div style="font-size:22px;font-weight:700;color:#1e293b;">{_fmt(today["total_cost"])}</div>
                </td>
                <td style="padding:12px;text-align:center;background:#faf5ff;border-radius:0 8px 8px 0;">
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Margin</div>
                    <div style="font-size:22px;font-weight:700;color:{margin_color};">{_pct(today["margin_pct"])}</div>
                </td>
            </tr>
        </table>

        <!-- Comparisons -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#f8fafc;border-radius:8px;margin-bottom:20px;">
            <tr>{comp_html}</tr>
        </table>

        <!-- Section Breakdown -->
        <h3 style="margin:0 0 10px;color:#1e293b;font-size:16px;">Sales by Section</h3>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="margin-bottom:20px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
            <tr style="background:#f8fafc;">
                <th style="padding:8px 12px;text-align:left;font-size:12px;color:#6b7280;">Section</th>
                <th style="padding:8px 12px;text-align:right;font-size:12px;color:#6b7280;">Sales</th>
                <th style="padding:8px 12px;text-align:right;font-size:12px;color:#6b7280;">Profit</th>
                <th style="padding:8px 12px;text-align:right;font-size:12px;color:#6b7280;">Share</th>
                <th style="padding:8px 4px;font-size:12px;color:#6b7280;width:100px;"></th>
            </tr>
            {_section_rows(sections)}
        </table>

        <!-- MTD -->
        {mtd_html}

        <!-- Expenses -->
        {exp_html}

    </div>

    <!-- Footer -->
    <div style="background:#f8fafc;padding:16px;text-align:center;border-top:1px solid #e5e7eb;">
        <div style="font-size:12px;color:#94a3b8;">
            Auto-generated by {BUSINESS_NAME} Automation
        </div>
    </div>

</div>
</body>
</html>'''
    return html
