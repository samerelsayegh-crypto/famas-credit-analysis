"""
FAMAS Premium Styles — Dark banking aesthetic with glassmorphism and gold accents.
"""


def get_premium_css():
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Global Reset ──────────────────────────────────────────────── */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .stApp {
        background: linear-gradient(145deg, #060e1a 0%, #0a1628 30%, #0d1b35 70%, #0a1628 100%) !important;
    }

    /* ── Sidebar ───────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #080f1e 0%, #0d1a30 100%) !important;
        border-right: 1px solid rgba(212, 168, 67, 0.15) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #d4a843 !important;
    }

    /* ── Header Bar ────────────────────────────────────────────────── */
    .famas-header {
        background: linear-gradient(135deg, rgba(13,27,53,0.95), rgba(20,40,70,0.9));
        border: 1px solid rgba(212,168,67,0.2);
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 28px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(212,168,67,0.1);
    }
    .famas-header h1 {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #d4a843 0%, #f0d68a 50%, #d4a843 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 4px 0;
    }
    .famas-header p {
        color: rgba(232,232,232,0.6);
        font-size: 0.9rem;
        margin: 0;
        font-weight: 300;
    }

    /* ── KPI Cards ─────────────────────────────────────────────────── */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 28px;
    }
    .kpi-card {
        background: linear-gradient(145deg, rgba(17,29,51,0.9), rgba(13,22,40,0.95));
        border: 1px solid rgba(212,168,67,0.12);
        border-radius: 14px;
        padding: 20px 22px;
        text-align: center;
        backdrop-filter: blur(15px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .kpi-card:hover {
        border-color: rgba(212,168,67,0.35);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(212,168,67,0.08);
    }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(212,168,67,0.7);
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #e8e8e8;
        line-height: 1.2;
    }
    .kpi-unit {
        font-size: 0.75rem;
        color: rgba(232,232,232,0.4);
        margin-top: 4px;
        font-weight: 400;
    }

    /* ── Status Badges ─────────────────────────────────────────────── */
    .badge-safe {
        background: rgba(0,230,118,0.15);
        color: #00e676;
        border: 1px solid rgba(0,230,118,0.3);
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-warning {
        background: rgba(255,193,7,0.15);
        color: #ffc107;
        border: 1px solid rgba(255,193,7,0.3);
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-danger {
        background: rgba(244,67,54,0.15);
        color: #f44336;
        border: 1px solid rgba(244,67,54,0.3);
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }

    /* ── Glass Panels ──────────────────────────────────────────────── */
    .glass-panel {
        background: linear-gradient(145deg, rgba(17,29,51,0.85), rgba(10,22,40,0.90));
        border: 1px solid rgba(212,168,67,0.1);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
        backdrop-filter: blur(15px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    .glass-panel h3 {
        color: #d4a843 !important;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 16px;
        letter-spacing: 0.3px;
    }

    /* ── Grade Badge ───────────────────────────────────────────────── */
    .grade-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        font-size: 1.8rem;
        font-weight: 900;
        letter-spacing: 1px;
        box-shadow: 0 0 30px rgba(0,0,0,0.3);
    }

    /* ── Scorecard Bars ────────────────────────────────────────────── */
    .score-bar-bg {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        height: 10px;
        overflow: hidden;
        margin-top: 6px;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.8s ease;
    }

    /* ── Data Tables ───────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] > div {
        border-radius: 12px !important;
    }

    /* ── Tabs Styling ──────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(13,27,53,0.5);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(212,168,67,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        color: rgba(232,232,232,0.6);
    }
    .stTabs [aria-selected="true"] {
        background: rgba(212,168,67,0.15) !important;
        color: #d4a843 !important;
        font-weight: 600;
    }

    /* ── Risk Flag Items ───────────────────────────────────────────── */
    .risk-flag {
        background: rgba(20,28,50,0.6);
        border-left: 3px solid;
        border-radius: 0 10px 10px 0;
        padding: 10px 16px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        color: #e8e8e8;
    }

    /* ── Upload Area ───────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(212,168,67,0.25) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        background: rgba(13,27,53,0.4) !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(212,168,67,0.5) !important;
    }

    /* ── Metric Override ───────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(17,29,51,0.9), rgba(13,22,40,0.95));
        border: 1px solid rgba(212,168,67,0.12);
        border-radius: 14px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] {
        color: rgba(212,168,67,0.7) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    [data-testid="stMetricValue"] {
        color: #e8e8e8 !important;
        font-weight: 700 !important;
    }

    /* ── Expander ───────────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        background: rgba(17,29,51,0.6) !important;
        border: 1px solid rgba(212,168,67,0.1) !important;
        border-radius: 12px !important;
    }

    /* ── Scrollbar ──────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(10,22,40,0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(212,168,67,0.3); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(212,168,67,0.5); }

    /* ── Hide Streamlit chrome ─────────────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }
    </style>
    """


def render_header(title: str, subtitle: str = ""):
    return f"""
    <div class="famas-header">
        <h1>🏦 {title}</h1>
        <p>{subtitle}</p>
    </div>
    """


def render_kpi_card(label: str, value: str, unit: str = ""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-unit">{unit}</div>
    </div>
    """


def render_grade_badge(grade: str, color: str, size: int = 80):
    return f"""
    <div class="grade-badge" style="
        width:{size}px; height:{size}px; font-size:{size*0.35}px;
        border: 3px solid {color};
        color: {color};
        background: rgba({_hex_to_rgb(color)}, 0.1);
    ">{grade}</div>
    """


def render_score_bar(label: str, score: float, weight: float, color: str = "#d4a843"):
    weighted = score * weight
    return f"""
    <div style="margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
            <span style="color:#e8e8e8; font-size:0.85rem; font-weight:500;">{label}</span>
            <span style="color:rgba(232,232,232,0.5); font-size:0.75rem;">{score:.0f}/100 (wt: {weight*100:.0f}% → {weighted:.1f})</span>
        </div>
        <div class="score-bar-bg">
            <div class="score-bar-fill" style="width:{min(score,100)}%; background: linear-gradient(90deg, {color}, {color}cc);"></div>
        </div>
    </div>
    """


def render_risk_flag(text: str):
    if "🔴" in text:
        border_color = "#f44336"
    elif "⚠" in text:
        border_color = "#ffc107"
    else:
        border_color = "#2196f3"
    return f'<div class="risk-flag" style="border-left-color:{border_color};">{text}</div>'


def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to RGB string."""
    h = hex_color.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
