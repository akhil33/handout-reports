"""Custom CSS theme for The Hangout dashboard."""

CUSTOM_CSS = """
<style>
/* ===== HIDE DEFAULT STREAMLIT CHROME ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Hide default multipage nav */
[data-testid="stSidebarNav"] {display: none !important;}

/* ===== SIDEBAR STYLING ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    padding-top: 0;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
}

/* Sidebar radio buttons — styled as nav items */
[data-testid="stSidebar"] .stRadio > div {
    gap: 2px !important;
}

[data-testid="stSidebar"] .stRadio > div > label {
    background: transparent !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    margin: 0 !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}

[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: rgba(255,255,255,0.08) !important;
}

[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: rgba(59,130,246,0.15) !important;
    border: 1px solid rgba(59,130,246,0.3) !important;
}

/* Hide radio circles */
[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
    display: none !important;
}

/* ===== MAIN CONTENT ===== */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

/* ===== KPI METRIC CARDS ===== */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

[data-testid="stMetric"] label {
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #1e293b !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}

/* ===== PAGE HEADERS ===== */
.main h1 {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #1e293b !important;
    margin-bottom: 0.5rem !important;
}

.main h2, .main .stSubheader {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #334155 !important;
}

.main h3 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
}

/* ===== ALERTS ===== */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-width: 0 0 0 4px !important;
}

/* ===== PLOTLY CHARTS ===== */
.stPlotlyChart {
    border-radius: 12px;
    overflow: hidden;
}

/* ===== PROGRESS BAR ===== */
.stProgress > div > div {
    border-radius: 8px !important;
    background-color: #e2e8f0 !important;
}

.stProgress > div > div > div {
    border-radius: 8px !important;
    background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
}

/* ===== BUTTONS ===== */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(59,130,246,0.2) !important;
    color: #93c5fd !important;
    border: 1px solid rgba(59,130,246,0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(59,130,246,0.35) !important;
    border-color: rgba(59,130,246,0.5) !important;
}

/* ===== EXPANDER ===== */
[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

/* ===== DIVIDER ===== */
.main hr {
    border-color: #e2e8f0 !important;
    margin: 1.5rem 0 !important;
}

/* ===== DATE INPUT ===== */
.stDateInput > div > div {
    border-radius: 8px !important;
}

/* ===== TAB STYLING ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    font-weight: 500;
}
</style>
"""

# Sidebar brand area HTML
SIDEBAR_BRAND = """
<div style="
    text-align: center;
    padding: 24px 16px 16px;
    margin: -1rem -1rem 0 -1rem;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
">
    <div style="
        font-size: 2.2rem;
        margin-bottom: 4px;
    ">🍺</div>
    <div style="
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        color: #f8fafc;
        text-transform: uppercase;
    ">The Hangout</div>
    <div style="
        font-size: 0.7rem;
        color: #64748b;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-top: 4px;
    ">Business Intelligence</div>
</div>
"""


def sidebar_kpi_card(label, value, delta=None, color="#3b82f6"):
    """Generate HTML for a mini KPI card in the sidebar."""
    delta_html = ""
    if delta:
        delta_color = "#4ade80" if not delta.startswith("-") else "#f87171"
        delta_html = f'<div style="font-size:0.7rem;color:{delta_color};margin-top:2px;">{delta}</div>'

    return f"""
    <div style="
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 12px 14px;
        border-left: 3px solid {color};
    ">
        <div style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
        <div style="font-size:1.2rem;font-weight:700;color:#f1f5f9;margin-top:2px;">{value}</div>
        {delta_html}
    </div>
    """


def page_header(title, subtitle=None):
    """Generate a styled page header."""
    sub = f'<p style="color:#64748b;font-size:0.9rem;margin-top:-8px;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin-bottom:1.5rem;">
        <h1 style="margin-bottom:0;padding-bottom:0;">{title}</h1>
        {sub}
    </div>
    """


NAV_ITEMS = {
    "Daily Overview": "📊",
    "Trends & Analytics": "📈",
    "Section Performance": "🏪",
    "Expenses & P&L": "💰",
}
