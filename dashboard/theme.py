"""Custom dark theme for The Hangout dashboard."""

CUSTOM_CSS = """
<style>
/* ===== HIDE DEFAULT STREAMLIT CHROME ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSidebarNav"] {display: none !important;}

header[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: none !important;
}

/* ===== GLOBAL DARK ===== */
.stApp {
    background-color: #0f172a;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1222 0%, #1e293b 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
    padding-top: 0;
}

[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
}

/* Nav radio buttons */
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
    background: rgba(255,255,255,0.06) !important;
}

[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: rgba(59,130,246,0.15) !important;
    border: 1px solid rgba(59,130,246,0.3) !important;
    color: #93c5fd !important;
}

[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
    display: none !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(59,130,246,0.15) !important;
    color: #93c5fd !important;
    border: 1px solid rgba(59,130,246,0.25) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(59,130,246,0.3) !important;
    border-color: rgba(59,130,246,0.5) !important;
}

[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

/* ===== MAIN CONTENT ===== */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

/* ===== KPI METRIC CARDS (dark) ===== */
[data-testid="stMetric"] {
    background: #1e293b;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}

/* ===== HEADINGS (dark) ===== */
.main h1 {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
    margin-bottom: 0.5rem !important;
}

.main h2, .main .stSubheader {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #e2e8f0 !important;
}

.main h3 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: #cbd5e1 !important;
}

/* ===== ALERTS ===== */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-width: 0 0 0 4px !important;
    background-color: #1e293b !important;
}

/* ===== PLOTLY CHARTS ===== */
.stPlotlyChart {
    border-radius: 12px;
    overflow: hidden;
}

/* ===== PROGRESS BAR ===== */
.stProgress > div > div {
    border-radius: 8px !important;
    background-color: #334155 !important;
}

.stProgress > div > div > div {
    border-radius: 8px !important;
    background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
}

/* ===== DIVIDER ===== */
.main hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 1.5rem 0 !important;
}

/* ===== INPUTS ===== */
.stDateInput > div > div {
    border-radius: 8px !important;
    background-color: #1e293b !important;
    border-color: rgba(255,255,255,0.1) !important;
}

/* ===== TABS ===== */
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

# Sidebar brand area
SIDEBAR_BRAND = """
<div style="
    text-align: center;
    padding: 24px 16px 16px;
    margin: -1rem -1rem 0 -1rem;
    background: linear-gradient(135deg, #0c1222 0%, #162032 100%);
    border-bottom: 1px solid rgba(255,255,255,0.06);
">
    <div style="font-size: 2.2rem; margin-bottom: 4px;">🍺</div>
    <div style="
        font-size: 1.4rem; font-weight: 800; letter-spacing: 0.1em;
        color: #f8fafc; text-transform: uppercase;
    ">The Hangout</div>
    <div style="
        font-size: 0.7rem; color: #64748b; letter-spacing: 0.15em;
        text-transform: uppercase; margin-top: 4px;
    ">Business Intelligence</div>
</div>
"""


def sidebar_kpi_card(label, value, delta=None, color="#3b82f6"):
    """Mini KPI card for sidebar."""
    delta_html = ""
    if delta:
        delta_color = "#4ade80" if not delta.startswith("-") else "#f87171"
        delta_html = f'<div style="font-size:0.7rem;color:{delta_color};margin-top:2px;">{delta}</div>'

    return f"""
    <div style="
        background: rgba(255,255,255,0.04);
        border-radius: 10px; padding: 12px 14px;
        border-left: 3px solid {color};
    ">
        <div style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">{label}</div>
        <div style="font-size:1.2rem;font-weight:700;color:#f1f5f9;margin-top:2px;">{value}</div>
        {delta_html}
    </div>
    """


NAV_ITEMS = {
    "Daily Overview": "📊",
    "Trends & Analytics": "📈",
    "Section Performance": "🏪",
    "Expenses & P&L": "💰",
}
