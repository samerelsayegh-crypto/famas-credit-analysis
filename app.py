"""
FAMAS — Financial Analysis & Credit Risk Assessment System
A professional-grade financial statement spreading and credit analysis tool.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import math

from engine.data_loader import load_excel_file, extract_financial_data, parse_three_statement_model
from engine.spreading import SpreadEngine
from engine.ratios import RatioEngine
from engine.credit_score import AltmanZScore, CreditScorecard, get_rating_grade
from engine.uca_cashflow import UCACashFlow
from styles import (
    get_premium_css, render_header, render_kpi_card,
    render_grade_badge, render_score_bar, render_risk_flag,
    _hex_to_rgb,
)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FAMAS — Credit Analysis System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_premium_css(), unsafe_allow_html=True)

# ── Plotly Theme ──────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#e8e8e8", size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(
        bgcolor="rgba(17,29,51,0.7)",
        bordercolor="rgba(212,168,67,0.15)",
        borderwidth=1,
        font=dict(size=11),
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.05)"),
)

COLORS = ["#d4a843", "#2d5a87", "#00e676", "#ff9800", "#e040fb", "#00bcd4", "#ff5252", "#69f0ae"]


def format_number(val, unit=""):
    """Format numbers for display."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "N/A"
    if unit == "%":
        return f"{val:.1f}%"
    elif unit == "x":
        return f"{val:.2f}x"
    elif unit == "days":
        return f"{val:.0f}"
    elif unit == "$" or abs(val) >= 1000:
        if abs(val) >= 1_000_000:
            return f"${val/1_000_000:,.1f}M"
        elif abs(val) >= 1000:
            return f"${val/1_000:,.0f}K"
        else:
            return f"${val:,.0f}"
    return f"{val:,.2f}"


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:2.2rem;">🏦</div>
        <div style="font-size:1.1rem; font-weight:800; color:#d4a843; letter-spacing:2px; margin-top:4px;">FAMAS</div>
        <div style="font-size:0.65rem; color:rgba(232,232,232,0.4); letter-spacing:1px; margin-top:2px;">CREDIT ANALYSIS SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Company Information
    st.markdown("### 📋 Company Information")
    company_name = st.text_input("Company Name", value="", placeholder="Enter company name…")
    industry = st.selectbox("Industry", [
        "Select Industry…", "Manufacturing", "Services", "Technology",
        "Healthcare", "Retail", "Energy", "Financial Services",
        "Real Estate", "Transportation", "Construction", "Other"
    ])
    fiscal_year_end = st.selectbox("Fiscal Year End", [
        "December", "January", "February", "March", "April", "May",
        "June", "July", "August", "September", "October", "November"
    ])
    currency = st.selectbox("Currency", ["USD ($)", "EUR (€)", "GBP (£)", "SAR (﷼)", "AED (د.إ)"])

    st.markdown("---")

    # File Upload
    st.markdown("### 📂 Upload Financial Statements")
    uploaded_file = st.file_uploader(
        "Upload Excel file (.xlsx)",
        type=["xlsx", "xls"],
        help="Upload a financial model with Income Statement, Balance Sheet, and Cash Flow data.",
    )

    # Demo data button
    import os
    demo_path = os.path.join(os.path.dirname(__file__), "CFI-Case-Study-Three-Statement-Model.xlsx")
    if os.path.exists(demo_path) and not st.session_state.get("processed"):
        if st.button("🎯 Load Demo Data", use_container_width=True, type="primary"):
            st.session_state["demo_file"] = demo_path
            st.rerun()

    # Z-Score model selection
    st.markdown("---")
    st.markdown("### ⚙️ Analysis Settings")
    z_model = st.radio("Altman Z-Score Model", ["Manufacturing", "Service"], index=0)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:10px; color:rgba(232,232,232,0.3); font-size:0.65rem;">
        FAMAS Credit Analysis System<br>
        Financial Statement Spreading & Risk Assessment<br>
        v2.0 — 2026
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# Navigation
NAV_ITEMS = ["📊 Dashboard", "📋 Financial Spreading", "📈 Ratio Analysis",
             "💳 Credit Scorecard", "💰 UCA Cash Flow", "📄 Executive Summary"]


def nav_page():
    cols = st.columns(len(NAV_ITEMS))
    selected = st.session_state.get("nav_page", NAV_ITEMS[0])
    for i, item in enumerate(NAV_ITEMS):
        with cols[i]:
            if st.button(item, key=f"nav_{i}", use_container_width=True,
                         type="primary" if item == selected else "secondary"):
                st.session_state["nav_page"] = item
                st.rerun()
    return st.session_state.get("nav_page", NAV_ITEMS[0])


# ── Process uploaded file or demo file ────────────────────────────────────────
file_to_process = uploaded_file
if file_to_process is None and st.session_state.get("demo_file"):
    file_to_process = st.session_state["demo_file"]

if file_to_process is not None and not st.session_state.get("processed"):
    try:
        sheets = load_excel_file(file_to_process)
        parsed = parse_three_statement_model(sheets)
        periods = parsed.get("periods", [])

        if not periods:
            st.error("❌ Could not detect financial periods in the uploaded file.")
            st.stop()

        # Build engines
        spreader = SpreadEngine(parsed)
        spreads = spreader.get_all_spreads()
        ratio_engine = RatioEngine(spreads, periods)
        uca_engine = UCACashFlow(spreads, periods)
        scorecard_engine = CreditScorecard()

        # Store in session
        st.session_state["processed"] = True
        st.session_state["periods"] = periods
        st.session_state["spreads"] = spreads
        st.session_state["parsed"] = parsed
        st.session_state["ratio_engine"] = ratio_engine
        st.session_state["uca_engine"] = uca_engine
        st.session_state["scorecard_engine"] = scorecard_engine

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.stop()


# ── Check if data is loaded ──────────────────────────────────────────────────
if not st.session_state.get("processed"):
    # Welcome screen
    st.markdown(render_header(
        "FAMAS Credit Analysis System",
        "Financial Analysis & Monitoring Assessment System — Upload financial statements to begin"
    ), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="glass-panel">
            <h3>📊 Financial Spreading</h3>
            <p style="color:rgba(232,232,232,0.6); font-size:0.85rem;">
                Standardize raw financial statements into FAMAS-format categories with common-size analysis and trend tracking.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="glass-panel">
            <h3>📈 30+ Financial Ratios</h3>
            <p style="color:rgba(232,232,232,0.6); font-size:0.85rem;">
                Comprehensive ratio analysis across profitability, leverage, liquidity, activity, and coverage dimensions.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="glass-panel">
            <h3>💳 Credit Risk Scoring</h3>
            <p style="color:rgba(232,232,232,0.6); font-size:0.85rem;">
                Altman Z-Score models and custom weighted credit scorecard with letter-grade ratings and risk commentary.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding:60px 0 30px 0;">
        <p style="color:rgba(232,232,232,0.4); font-size:1rem;">
            ← Upload an Excel file in the sidebar to begin analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# DATA IS LOADED — Render Pages
# ══════════════════════════════════════════════════════════════════════════════

periods = st.session_state["periods"]
spreads = st.session_state["spreads"]
ratio_engine = st.session_state["ratio_engine"]
uca_engine = st.session_state["uca_engine"]
scorecard_engine = st.session_state["scorecard_engine"]

display_name = company_name if company_name else "Company Analysis"

# Navigation
current_page = nav_page()

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 1: DASHBOARD                                                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if current_page == "📊 Dashboard":
    st.markdown(render_header(
        f"{display_name} — Dashboard",
        f"Financial overview • Periods: {periods[0]} – {periods[-1]} • {len(periods)} periods analyzed"
    ), unsafe_allow_html=True)

    # ── Z-Score & Credit Grade ────────────────────────────────────────────
    latest = periods[-1]
    is_df = spreads["income_statement"]
    bs_df = spreads["balance_sheet"]

    from engine.ratios import _get_val
    # Working capital: try direct, then derive from components
    tca = _get_val(bs_df, "Total Current Assets", latest)
    tcl = _get_val(bs_df, "Total Current Liabilities", latest)
    if tca == 0 and tcl == 0:
        # Derive from individual current items
        tca = sum(_get_val(bs_df, item, latest) for item in
                  ["Cash & Equivalents", "Accounts Receivable", "Inventory",
                   "Prepaid Expenses", "Other Current Assets"])
        tcl = sum(_get_val(bs_df, item, latest) for item in
                  ["Accounts Payable", "Accrued Liabilities",
                   "Short-Term Debt", "Current Portion of LT Debt",
                   "Other Current Liabilities"])
    wc = tca - tcl
    ta = _get_val(bs_df, "Total Assets", latest)
    re = _get_val(bs_df, "Retained Earnings", latest)
    # EBIT: try direct, then derive from EBT + Interest
    ebit = _get_val(is_df, "EBIT", latest)
    if ebit == 0:
        ebt = _get_val(is_df, "EBT", latest)
        interest = _get_val(is_df, "Interest Expense", latest)
        ebit = ebt + abs(interest)
    equity = _get_val(bs_df, "Total Equity", latest)
    tl = _get_val(bs_df, "Total Liabilities", latest)
    rev = _get_val(is_df, "Revenue", latest)

    z_result = AltmanZScore.calculate(wc, ta, re, ebit, equity, tl, rev, z_model.lower())
    scorecard_result = scorecard_engine.calculate(ratio_engine, periods)
    key_metrics = ratio_engine.get_key_metrics()

    # ── KPI Row ───────────────────────────────────────────────────────────
    z_val = z_result.get("z_score")
    z_zone = z_result.get("zone", "N/A")
    z_color = "#00e676" if z_zone == "Safe Zone" else ("#ffc107" if z_zone == "Grey Zone" else "#f44336")

    grade = scorecard_result.get("grade", "NR")
    grade_color = scorecard_result.get("grade_color", "#757575")
    total_score = scorecard_result.get("total_score", 0)

    # Build KPI data list
    kpi_items = [
        ("Altman Z-Score",
         f'<span style="color:{z_color}">{z_val:.2f}</span>' if z_val else "N/A",
         z_zone),
        ("Credit Grade",
         f'<span style="color:{grade_color}">{grade}</span>',
         f"Score: {total_score:.0f}/100"),
    ]
    for name, data in key_metrics.items():
        val = data["value"]
        fmt = data["format"]
        if val is not None:
            if fmt == "%":
                display_val = f"{val*100:.1f}%"
            elif fmt == "x":
                display_val = f"{val:.2f}x"
            else:
                display_val = format_number(val)
        else:
            display_val = "N/A"
        kpi_items.append((name, display_val, ""))

    kpi_cols = st.columns(len(kpi_items))
    for i, (label, value, unit) in enumerate(kpi_items):
        with kpi_cols[i]:
            st.markdown(render_kpi_card(label, value, unit), unsafe_allow_html=True)

    # ── Charts Row ────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="glass-panel"><h3>📊 Revenue & Profitability Trend</h3></div>', unsafe_allow_html=True)
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        rev_data = [_get_val(is_df, "Revenue", p) for p in periods]
        gp_data = [_get_val(is_df, "Gross Profit", p) for p in periods]
        ni_data = [_get_val(is_df, "Net Income", p) for p in periods]

        fig.add_trace(go.Bar(x=periods, y=rev_data, name="Revenue",
            marker_color="#2d5a87", opacity=0.7), secondary_y=False)
        fig.add_trace(go.Scatter(x=periods, y=gp_data, name="Gross Profit",
            line=dict(color="#d4a843", width=3), mode="lines+markers"), secondary_y=False)
        fig.add_trace(go.Scatter(x=periods, y=ni_data, name="Net Income",
            line=dict(color="#00e676", width=2, dash="dot"), mode="lines+markers"), secondary_y=False)

        fig.update_layout(**PLOTLY_LAYOUT, height=380, title_text="")
        fig.update_yaxes(title_text="Amount ($K)", secondary_y=False, gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="glass-panel"><h3>💳 Credit Scorecard Breakdown</h3></div>', unsafe_allow_html=True)

        dims = scorecard_result.get("dimensions", {})
        if dims:
            categories = list(dims.keys())
            values = [dims[c]["score"] for c in categories]

            fig = go.Figure(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                fillcolor='rgba(212,168,67,0.15)',
                line=dict(color='#d4a843', width=2),
                marker=dict(size=8, color='#d4a843'),
            ))
            fig.update_layout(
                **PLOTLY_LAYOUT,
                height=380,
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0, 100],
                        gridcolor="rgba(255,255,255,0.08)", linecolor="rgba(255,255,255,0.08)",
                        tickfont=dict(color="rgba(232,232,232,0.4)", size=10)),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                        linecolor="rgba(255,255,255,0.08)",
                        tickfont=dict(color="#e8e8e8", size=11)),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Z-Score Components ────────────────────────────────────────────────
    with st.expander("🔍 Altman Z-Score Components", expanded=False):
        comps = z_result.get("components", {})
        if comps:
            comp_cols = st.columns(len(comps))
            for i, (name, val) in enumerate(comps.items()):
                with comp_cols[i]:
                    st.metric(name, f"{val:.4f}")

    # ── Risk Flags ────────────────────────────────────────────────────────
    flags = scorecard_result.get("flags", [])
    if flags:
        st.markdown('<div class="glass-panel"><h3>⚠️ Risk Flags & Commentary</h3></div>', unsafe_allow_html=True)
        for flag in flags:
            st.markdown(render_risk_flag(flag), unsafe_allow_html=True)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 2: FINANCIAL SPREADING                                              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

elif current_page == "📋 Financial Spreading":
    st.markdown(render_header(
        f"{display_name} — Financial Spreading",
        "Standardized financial statements with common-size analysis"
    ), unsafe_allow_html=True)

    spread_tabs = st.tabs(["📊 Income Statement", "📋 Balance Sheet", "💰 Cash Flow Statement"])

    for tab_idx, (tab, key, title) in enumerate(zip(
        spread_tabs,
        ["income_statement", "balance_sheet", "cash_flow"],
        ["Income Statement", "Balance Sheet", "Cash Flow Statement"]
    )):
        with tab:
            df = spreads.get(key, pd.DataFrame())
            if df.empty:
                st.info(f"No {title} data available.")
                continue

            # Format the display
            display_df = df.copy()
            cols_to_show = ["Category"] + [c for c in display_df.columns
                           if c not in ("Category", "Original Label") and "%" not in str(c)]
            pct_cols = [c for c in display_df.columns if "%" in str(c)]

            # Absolute values table
            st.markdown(f"**{title} — Absolute Values**")
            abs_df = display_df[cols_to_show].copy()
            # Format numeric columns
            for col in cols_to_show[1:]:
                abs_df[col] = abs_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "—")
            st.dataframe(abs_df, use_container_width=True, hide_index=True, height=400)

            # Common-size analysis
            if pct_cols:
                st.markdown(f"**{title} — Common-Size Analysis (%)**")
                cs_cols = ["Category"] + pct_cols
                cs_df = display_df[cs_cols].copy()
                for col in pct_cols:
                    cs_df[col] = cs_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
                st.dataframe(cs_df, use_container_width=True, hide_index=True, height=400)

            # Trend chart
            st.markdown(f"**{title} — Trend Visualization**")
            chart_df = display_df[cols_to_show].set_index("Category")
            # Pick key rows for chart
            chart_df_t = chart_df.T
            chart_df_t.index.name = "Period"
            fig = go.Figure()
            for i, col in enumerate(chart_df_t.columns[:8]):  # Max 8 series
                fig.add_trace(go.Scatter(
                    x=chart_df_t.index, y=chart_df_t[col],
                    name=col[:30], line=dict(color=COLORS[i % len(COLORS)], width=2),
                    mode="lines+markers",
                ))
            fig.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 3: RATIO ANALYSIS                                                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

elif current_page == "📈 Ratio Analysis":
    st.markdown(render_header(
        f"{display_name} — Ratio Analysis",
        f"30+ financial ratios across 5 categories • {len(periods)} periods"
    ), unsafe_allow_html=True)

    all_ratios = ratio_engine.calculate_all()

    ratio_tabs = st.tabs(list(all_ratios.keys()))

    for tab, (category, ratio_df) in zip(ratio_tabs, all_ratios.items()):
        with tab:
            if ratio_df.empty:
                st.info(f"No data for {category}")
                continue

            # Ratio table
            display_df = ratio_df.copy()
            for p in periods:
                if p in display_df.columns:
                    display_df[p] = display_df.apply(
                        lambda r: format_number(r[p], r["Unit"]) if pd.notna(r.get(p)) else "—",
                        axis=1
                    )
            show_cols = ["Ratio"] + [p for p in periods if p in display_df.columns]
            st.dataframe(display_df[show_cols], use_container_width=True, hide_index=True, height=350)

            # Trend charts
            st.markdown(f"**{category} — Trend Charts**")
            raw_df = ratio_df.copy()
            num_ratios = len(raw_df)
            n_cols = min(3, num_ratios)
            chart_cols = st.columns(n_cols)

            for i, (_, row) in enumerate(raw_df.iterrows()):
                with chart_cols[i % n_cols]:
                    name = row["Ratio"]
                    unit = row["Unit"]
                    vals = [row.get(p) for p in periods]

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=periods, y=vals, mode="lines+markers+text",
                        line=dict(color=COLORS[i % len(COLORS)], width=2.5),
                        marker=dict(size=7),
                        text=[format_number(v, unit) if v is not None else "" for v in vals],
                        textposition="top center",
                        textfont=dict(size=9, color="rgba(232,232,232,0.7)"),
                    ))
                    fig.update_layout(
                        **PLOTLY_LAYOUT,
                        height=220,
                        title=dict(text=name, font=dict(size=12, color="#d4a843")),
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 4: CREDIT SCORECARD                                                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝

elif current_page == "💳 Credit Scorecard":
    st.markdown(render_header(
        f"{display_name} — Credit Scorecard",
        "Comprehensive credit risk assessment with Altman Z-Score and custom weighted scorecard"
    ), unsafe_allow_html=True)

    latest = periods[-1]
    is_df = spreads["income_statement"]
    bs_df = spreads["balance_sheet"]
    from engine.ratios import _get_val

    # Working capital: try direct, then derive from components
    tca = _get_val(bs_df, "Total Current Assets", latest)
    tcl = _get_val(bs_df, "Total Current Liabilities", latest)
    if tca == 0 and tcl == 0:
        tca = sum(_get_val(bs_df, item, latest) for item in
                  ["Cash & Equivalents", "Accounts Receivable", "Inventory",
                   "Prepaid Expenses", "Other Current Assets"])
        tcl = sum(_get_val(bs_df, item, latest) for item in
                  ["Accounts Payable", "Accrued Liabilities",
                   "Short-Term Debt", "Current Portion of LT Debt",
                   "Other Current Liabilities"])
    wc = tca - tcl
    ta = _get_val(bs_df, "Total Assets", latest)
    re = _get_val(bs_df, "Retained Earnings", latest)
    ebit = _get_val(is_df, "EBIT", latest)
    if ebit == 0:
        ebt = _get_val(is_df, "EBT", latest)
        interest = _get_val(is_df, "Interest Expense", latest)
        ebit = ebt + abs(interest)
    equity = _get_val(bs_df, "Total Equity", latest)
    tl = _get_val(bs_df, "Total Liabilities", latest)
    rev = _get_val(is_df, "Revenue", latest)

    z_result = AltmanZScore.calculate(wc, ta, re, ebit, equity, tl, rev, z_model.lower())
    scorecard_result = scorecard_engine.calculate(ratio_engine, periods)

    # ── Score Overview Row ────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        grade = scorecard_result["grade"]
        color = scorecard_result["grade_color"]
        desc = scorecard_result["grade_description"]
        total = scorecard_result["total_score"]

        st.markdown(f"""<div class="glass-panel" style="text-align:center;">
            <h3 style="color:#d4a843;">Credit Rating</h3>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div style="text-align:center; margin:20px 0;">
            <span style="display:inline-flex; align-items:center; justify-content:center;
                width:100px; height:100px; font-size:35px; font-weight:900;
                border:3px solid {color}; border-radius:50%; color:{color};
                background:rgba({_hex_to_rgb(color)}, 0.1);">{grade}</span>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div style="text-align:center;">
            <div style="font-size:1.3rem; font-weight:700; color:#e8e8e8; margin:12px 0;">{total:.0f} / 100</div>
            <p style="color:rgba(232,232,232,0.5); font-size:0.8rem; line-height:1.5;">{desc}</p>
        </div>""", unsafe_allow_html=True)

    with col2:
        z_val = z_result.get("z_score")
        z_zone = z_result.get("zone", "N/A")
        z_model_name = z_result.get("model", "manufacturing").title()
        z_color = "#00e676" if z_zone == "Safe Zone" else ("#ffc107" if z_zone == "Grey Zone" else "#f44336")
        z_display = f"{z_val:.2f}" if z_val is not None else "N/A"

        badge_class = "badge-safe" if z_zone == "Safe Zone" else ("badge-warning" if z_zone == "Grey Zone" else "badge-danger")

        st.markdown(f"""<div class="glass-panel" style="text-align:center;">
            <h3 style="color:#d4a843;">Altman Z-Score</h3>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div style="text-align:center;">
            <div style="font-size:3rem; font-weight:900; color:{z_color}; margin:20px 0;">{z_display}</div>
            <span class="{badge_class}">{z_zone}</span>
            <p style="color:rgba(232,232,232,0.4); font-size:0.75rem; margin-top:12px;">Model: {z_model_name}</p>
        </div>""", unsafe_allow_html=True)

    with col3:
        safe_threshold = "2.99" if z_model == "Manufacturing" else "2.60"
        st.markdown(f"""<div class="glass-panel">
            <h3 style="color:#d4a843;">Z-Score Zones</h3>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin-top:12px;">
            <div style="display:flex; align-items:center; margin-bottom:10px;">
                <div style="width:12px; height:12px; border-radius:50%; background:#00e676; margin-right:10px;"></div>
                <span style="color:#e8e8e8; font-size:0.85rem;"><b>Safe Zone</b> (Z &gt; {safe_threshold})</span>
            </div>
            <div style="display:flex; align-items:center; margin-bottom:10px;">
                <div style="width:12px; height:12px; border-radius:50%; background:#ffc107; margin-right:10px;"></div>
                <span style="color:#e8e8e8; font-size:0.85rem;"><b>Grey Zone</b> (watch carefully)</span>
            </div>
            <div style="display:flex; align-items:center; margin-bottom:10px;">
                <div style="width:12px; height:12px; border-radius:50%; background:#f44336; margin-right:10px;"></div>
                <span style="color:#e8e8e8; font-size:0.85rem;"><b>Distress Zone</b> (high default risk)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Dimension Scores ──────────────────────────────────────────────────
    st.markdown('<div class="glass-panel"><h3>📊 Scorecard Dimensions</h3></div>', unsafe_allow_html=True)
    dims = scorecard_result.get("dimensions", {})
    for dim_name, dim_data in dims.items():
        score = dim_data["score"]
        weight = dim_data["weight"]
        color = "#00e676" if score >= 75 else ("#d4a843" if score >= 50 else ("#ff9800" if score >= 25 else "#f44336"))
        st.markdown(render_score_bar(dim_name, score, weight, color), unsafe_allow_html=True)

    # ── Z-Score Components ────────────────────────────────────────────────
    st.markdown('<div class="glass-panel"><h3>🧮 Z-Score Component Analysis</h3></div>', unsafe_allow_html=True)
    comps = z_result.get("components", {})
    comp_names = list(comps.keys())
    comp_vals = list(comps.values())

    fig = go.Figure(go.Bar(
        x=comp_names, y=comp_vals,
        marker_color=[COLORS[i % len(COLORS)] for i in range(len(comp_names))],
        text=[f"{v:.4f}" for v in comp_vals],
        textposition='outside',
        textfont=dict(color="#e8e8e8"),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # ── Risk Flags ────────────────────────────────────────────────────────
    flags = scorecard_result.get("flags", [])
    if flags:
        st.markdown('<div class="glass-panel"><h3>⚠️ Risk Flags & Analyst Commentary</h3></div>', unsafe_allow_html=True)
        for flag in flags:
            st.markdown(render_risk_flag(flag), unsafe_allow_html=True)
    else:
        st.success("✅ No critical risk flags identified.")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 5: UCA CASH FLOW                                                    ║
# ╚════════════════════════════════════════════════════════════════════════════╝

elif current_page == "💰 UCA Cash Flow":
    st.markdown(render_header(
        f"{display_name} — UCA Cash Flow Analysis",
        "Uniform Credit Analysis cash flow format — Focus on debt service capacity"
    ), unsafe_allow_html=True)

    uca_df = uca_engine.build()
    if uca_df.empty:
        st.info("Insufficient data for UCA Cash Flow analysis.")
    else:
        # Transpose for display (periods as columns)
        display_data = uca_df.set_index("period").T
        display_data.index.name = "Line Item"

        # Format values
        formatted = display_data.copy()
        for col in formatted.columns:
            formatted[col] = formatted[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "—")

        st.dataframe(formatted, use_container_width=True, height=500)

        # ── Waterfall Chart ───────────────────────────────────────────────
        st.markdown('<div class="glass-panel"><h3>💧 UCA Cash Flow Waterfall (Latest Period)</h3></div>', unsafe_allow_html=True)

        latest_uca = uca_df.iloc[-1]
        waterfall_items = [
            ("Net Sales", latest_uca.get("Net Sales / Revenue", 0)),
            ("Δ AR", latest_uca.get("(-) Change in AR", 0)),
            ("Cash COGS", latest_uca.get("(-) Cash Cost of Goods Sold", 0)),
            ("Cash OpEx", latest_uca.get("(-) Cash Operating Expenses", 0)),
            ("Tax", latest_uca.get("(-) Income Tax", 0)),
            ("Interest", latest_uca.get("(-) Interest Expense", 0)),
            ("CapEx", latest_uca.get("(-) Capital Expenditures", 0)),
            ("Debt Δ", latest_uca.get("(+/-) Debt Issuance/Repayment", 0)),
            ("Equity Δ", latest_uca.get("(+/-) Equity Issuance/Repayment", 0)),
        ]

        labels = [item[0] for item in waterfall_items] + ["Surplus/(Deficit)"]
        values = [item[1] for item in waterfall_items]
        measures = ["absolute"] + ["relative"] * (len(values) - 1) + ["total"]
        values.append(0)  # total is calculated

        colors_wf = []
        for v in values[:-1]:
            colors_wf.append("#00e676" if v >= 0 else "#f44336")
        surplus = latest_uca.get("= Financing Surplus / (Deficit)", 0)
        colors_wf.append("#d4a843")

        fig = go.Figure(go.Waterfall(
            x=labels, y=values, measure=measures,
            connector=dict(line=dict(color="rgba(212,168,67,0.3)", width=1)),
            increasing=dict(marker_color="#00e676"),
            decreasing=dict(marker_color="#f44336"),
            totals=dict(marker_color="#d4a843"),
            textposition="outside",
            text=[f"{v:,.0f}" for v in values[:-1]] + [f"{surplus:,.0f}"],
            textfont=dict(color="#e8e8e8", size=10),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # ── Summary Metrics ───────────────────────────────────────────────
        st.markdown('<div class="glass-panel"><h3>📊 UCA Key Metrics (Latest Period)</h3></div>', unsafe_allow_html=True)
        summary = uca_engine.get_summary_metrics()
        if summary:
            metric_cols = st.columns(len(summary))
            for i, (name, val) in enumerate(summary.items()):
                with metric_cols[i]:
                    color = "normal" if val >= 0 else "inverse"
                    st.metric(name, format_number(val, "$"))


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PAGE 6: EXECUTIVE SUMMARY                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

elif current_page == "📄 Executive Summary":
    st.markdown(render_header(
        f"{display_name} — Executive Summary",
        "Auto-generated credit analysis report"
    ), unsafe_allow_html=True)

    latest = periods[-1]
    from engine.ratios import _get_val
    is_df = spreads["income_statement"]
    bs_df = spreads["balance_sheet"]

    rev = _get_val(is_df, "Revenue", latest)
    ni = _get_val(is_df, "Net Income", latest)
    ta = _get_val(bs_df, "Total Assets", latest)
    equity = _get_val(bs_df, "Total Equity", latest)
    tl = _get_val(bs_df, "Total Liabilities", latest)
    wc = _get_val(bs_df, "Total Current Assets", latest) - _get_val(bs_df, "Total Current Liabilities", latest)
    re_val = _get_val(bs_df, "Retained Earnings", latest)
    ebit = _get_val(is_df, "EBIT", latest)

    z_result = AltmanZScore.calculate(wc, ta, re_val, ebit, equity, tl, rev, z_model.lower())
    scorecard_result = scorecard_engine.calculate(ratio_engine, periods)

    grade = scorecard_result["grade"]
    grade_color = scorecard_result["grade_color"]
    total_score = scorecard_result["total_score"]
    z_val = z_result.get("z_score") or 0
    z_zone = z_result.get("zone", "N/A")

    # Revenue growth
    if len(periods) >= 2:
        rev_prev = _get_val(is_df, "Revenue", periods[-2])
        rev_growth = ((rev - rev_prev) / rev_prev * 100) if rev_prev > 0 else 0
    else:
        rev_growth = 0

    gm = ratio_engine.gross_margin(latest) or 0
    nm = ratio_engine.net_margin(latest) or 0
    cr = ratio_engine.current_ratio(latest) or 0
    de = ratio_engine.debt_to_equity(latest) or 0
    ic = ratio_engine.interest_coverage(latest) or 0

    # ── Report ────────────────────────────────────────────────────────────
    # ── Header ─────────────────────────────────────────────────────────
    st.markdown(f"""<div class="glass-panel">
        <h3>📋 Credit Analysis Report</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; padding-bottom:16px; border-bottom:1px solid rgba(212,168,67,0.15);">
            <div>
                <div style="font-size:1.3rem; font-weight:700; color:#e8e8e8;">{display_name}</div>
                <div style="color:rgba(232,232,232,0.5); font-size:0.85rem;">
                    Industry: {industry} • FY End: {fiscal_year_end} • Currency: {currency}
                </div>
            </div>
            <div style="text-align:center;">
                <span style="display:inline-flex; align-items:center; justify-content:center;
                    width:70px; height:70px; font-size:24px; font-weight:900;
                    border:3px solid {grade_color}; border-radius:50%; color:{grade_color};
                    background:rgba({_hex_to_rgb(grade_color)}, 0.1);">{grade}</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Overview ──────────────────────────────────────────────────────
    company_label = company_name if company_name else "The company"
    overview_commentary = "increase" if rev_growth >= 0 else "decline"
    st.markdown(f"""<div style="color:#e8e8e8; font-size:0.9rem; line-height:1.8; padding:0 16px;">
        <p><b style="color:#d4a843;">Overview:</b>
            {company_label} reported revenue of
            <b>{format_number(rev, "$")}</b> for fiscal year {latest}, representing a
            <b>{rev_growth:+.1f}%</b> year-over-year {overview_commentary}.
            Net income was <b>{format_number(ni, "$")}</b>, translating to a net margin of
            <b>{nm*100:.1f}%</b>.
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Profitability ─────────────────────────────────────────────────
    gm_comment = "which is healthy and indicates strong pricing power." if gm > 0.30 else "which suggests moderate cost pressure." if gm > 0.15 else "which indicates significant cost pressure."
    nm_comment = "strong" if nm > 0.10 else "adequate" if nm > 0.03 else "weak"
    st.markdown(f"""<div style="color:#e8e8e8; font-size:0.9rem; line-height:1.8; padding:0 16px;">
        <p><b style="color:#d4a843;">Profitability:</b>
            Gross margin stands at <b>{gm*100:.1f}%</b>
            {gm_comment}
            Net profitability is {nm_comment}.
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Balance Sheet ─────────────────────────────────────────────────
    de_comment = "— indicating conservative leverage." if de < 1.0 else "— indicating moderate leverage." if de < 2.0 else "— indicating elevated leverage that warrants monitoring."
    st.markdown(f"""<div style="color:#e8e8e8; font-size:0.9rem; line-height:1.8; padding:0 16px;">
        <p><b style="color:#d4a843;">Balance Sheet:</b>
            Total assets are <b>{format_number(ta, "$")}</b> with total equity of <b>{format_number(equity, "$")}</b>.
            The debt-to-equity ratio is <b>{de:.2f}x</b>
            {de_comment}
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Liquidity ─────────────────────────────────────────────────────
    cr_comment = "which is strong, indicating comfortable short-term liquidity." if cr > 1.5 else "which is adequate." if cr > 1.0 else "which is concerning and may indicate liquidity stress."
    st.markdown(f"""<div style="color:#e8e8e8; font-size:0.9rem; line-height:1.8; padding:0 16px;">
        <p><b style="color:#d4a843;">Liquidity:</b>
            The current ratio is <b>{cr:.2f}x</b>
            {cr_comment}
            Working capital is <b>{format_number(wc, "$")}</b>.
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Coverage ──────────────────────────────────────────────────────
    ic_comment = "— very comfortable coverage of debt obligations." if ic > 3.0 else "— adequate but should be monitored." if ic > 1.5 else "— concerning. The company may struggle to service its debt."
    st.markdown(f"""<div style="color:#e8e8e8; font-size:0.9rem; line-height:1.8; padding:0 16px;">
        <p><b style="color:#d4a843;">Coverage:</b>
            Interest coverage stands at <b>{ic:.1f}x</b>
            {ic_comment}
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Credit Assessment ─────────────────────────────────────────────
    z_comment = "This suggests a low probability of financial distress." if z_zone == "Safe Zone" else "Continued monitoring is recommended." if z_zone == "Grey Zone" else "Immediate attention is warranted to address financial distress indicators."
    st.markdown(f"""<div style="color:#e8e8e8; font-size:0.9rem; line-height:1.8; padding:0 16px;">
        <p><b style="color:#d4a843;">Credit Assessment:</b>
            The overall credit score is <b>{total_score:.0f}/100</b>, corresponding to a
            <b style="color:{grade_color};">{grade}</b> rating.
            The Altman Z-Score is <b>{z_val:.2f}</b>, placing the company in the
            <b>{z_zone}</b>.
            {z_comment}
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Risk Flags ────────────────────────────────────────────────────────
    flags = scorecard_result.get("flags", [])
    if flags:
        st.markdown('<div class="glass-panel"><h3>⚠️ Key Risk Flags</h3></div>', unsafe_allow_html=True)
        for flag in flags:
            st.markdown(render_risk_flag(flag), unsafe_allow_html=True)

    # ── Summary Table ─────────────────────────────────────────────────────
    st.markdown('<div class="glass-panel"><h3>📊 Financial Snapshot</h3></div>', unsafe_allow_html=True)

    snapshot_data = {
        "Metric": ["Revenue", "Net Income", "Total Assets", "Total Equity",
                    "Gross Margin", "Net Margin", "ROE", "Current Ratio",
                    "Debt/Equity", "Interest Coverage", "Z-Score", "Credit Grade"],
        "Value": [
            format_number(rev, "$"), format_number(ni, "$"),
            format_number(ta, "$"), format_number(equity, "$"),
            f"{gm*100:.1f}%" if gm else "N/A", f"{nm*100:.1f}%" if nm else "N/A",
            f"{ratio_engine.roe(latest)*100:.1f}%" if ratio_engine.roe(latest) else "N/A",
            f"{cr:.2f}x" if cr else "N/A",
            f"{de:.2f}x" if de else "N/A",
            f"{ic:.1f}x" if ic else "N/A",
            f"{z_val:.2f}" if z_val else "N/A",
            grade,
        ],
    }
    st.dataframe(pd.DataFrame(snapshot_data), use_container_width=True, hide_index=True)

    # ── Export ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Export Report")

    col1, col2 = st.columns(2)
    with col1:
        # CSV export of all ratios
        all_ratios = ratio_engine.calculate_all()
        all_ratio_rows = []
        for cat, df in all_ratios.items():
            for _, row in df.iterrows():
                r = {"Category": cat, "Ratio": row["Ratio"], "Unit": row["Unit"]}
                for p in periods:
                    r[p] = row.get(p, "")
                all_ratio_rows.append(r)
        export_df = pd.DataFrame(all_ratio_rows)
        csv_data = export_df.to_csv(index=False)
        st.download_button(
            "📊 Download Ratios (CSV)",
            csv_data,
            file_name=f"FAMAS_{display_name.replace(' ', '_')}_Ratios.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        # Full spreading export
        all_spread_rows = []
        for section, df in spreads.items():
            if not df.empty:
                for _, row in df.iterrows():
                    r = {"Section": section.replace("_", " ").title(), "Category": row.get("Category", "")}
                    for p in periods:
                        r[p] = row.get(p, "")
                    all_spread_rows.append(r)
        spread_export = pd.DataFrame(all_spread_rows)
        csv_spread = spread_export.to_csv(index=False)
        st.download_button(
            "📋 Download Spreadings (CSV)",
            csv_spread,
            file_name=f"FAMAS_{display_name.replace(' ', '_')}_Spreadings.csv",
            mime="text/csv",
            use_container_width=True,
        )
