"""
FAMAS Data Loader — Ingests Excel financial statements and standardizes them.
"""
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional


# ── Canonical line-item mappings ──────────────────────────────────────────────
INCOME_STATEMENT_KEYWORDS = [
    "revenue", "sales", "net revenue", "total revenue",
    "cost of goods", "cogs", "cost of sales",
    "gross profit",
    "operating", "expense", "depreciation", "amortization",
    "ebitda", "ebit", "earnings before",
    "interest expense", "income tax", "tax",
    "net income", "net earnings", "net profit",
]

BALANCE_SHEET_KEYWORDS = [
    "cash", "accounts receivable", "inventory", "prepaid",
    "current assets", "total assets",
    "property", "plant", "equipment", "pp&e", "ppe",
    "intangible", "goodwill",
    "accounts payable", "accrued", "short-term debt", "current portion",
    "current liabilities", "total liabilities",
    "long-term debt", "notes payable",
    "retained earnings", "common stock", "shareholder", "equity",
    "total liabilities & shareholder",
]

CASH_FLOW_KEYWORDS = [
    "cash from operations", "operating cash",
    "cash from investing", "investing cash",
    "cash from financing", "financing cash",
    "capital expenditure", "capex",
    "net increase", "net decrease", "net change in cash",
    "opening cash", "closing cash",
    "depreciation", "working capital",
]


def load_excel_file(file) -> Dict[str, pd.DataFrame]:
    """Load an Excel file and return a dict of sheet_name → DataFrame."""
    xls = pd.ExcelFile(file, engine="openpyxl")
    sheets = {}
    for name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=name, header=None)
        sheets[name] = df
    return sheets


def detect_statement_type(df: pd.DataFrame) -> str:
    """Auto-classify a DataFrame as 'income_statement', 'balance_sheet', 'cash_flow', or 'unknown'."""
    text = " ".join(str(v).lower() for v in df.iloc[:, 0].dropna().values)

    scores = {
        "income_statement": sum(1 for kw in INCOME_STATEMENT_KEYWORDS if kw in text),
        "balance_sheet": sum(1 for kw in BALANCE_SHEET_KEYWORDS if kw in text),
        "cash_flow": sum(1 for kw in CASH_FLOW_KEYWORDS if kw in text),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "unknown"


def _find_year_row(df: pd.DataFrame) -> Optional[int]:
    """Find the row index that contains year labels (e.g. 2020, 2021, …)."""
    for idx, row in df.iterrows():
        year_count = 0
        for val in row:
            try:
                v = int(float(val))
                if 1990 <= v <= 2040:
                    year_count += 1
            except (ValueError, TypeError):
                continue
        if year_count >= 2:
            return idx
    return None


def _clean_label(val) -> str:
    """Normalize a row label string."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_financial_data(df: pd.DataFrame) -> Tuple[List[str], pd.DataFrame]:
    """
    From a raw sheet DataFrame, extract:
      - periods: list of year/period labels (column headers)
      - data: DataFrame with 'label' column and one column per period
    """
    year_row_idx = _find_year_row(df)
    if year_row_idx is None:
        # Fallback: assume first row is header
        year_row_idx = 0

    year_row = df.iloc[year_row_idx]
    periods = []
    period_cols = []
    for col_idx, val in enumerate(year_row):
        try:
            v = int(float(val))
            if 1990 <= v <= 2040:
                periods.append(str(v))
                period_cols.append(col_idx)
        except (ValueError, TypeError):
            continue

    if not periods:
        return [], pd.DataFrame()

    # Extract data rows below the year row
    label_col = 0  # labels in first column
    rows = []
    for idx in range(year_row_idx + 1, len(df)):
        label = _clean_label(df.iloc[idx, label_col])
        if not label:
            continue
        # Skip rows that are section headers with no data
        values = []
        has_data = False
        for pc in period_cols:
            val = df.iloc[idx, pc]
            if pd.notna(val):
                try:
                    values.append(float(val))
                    has_data = True
                except (ValueError, TypeError):
                    values.append(0.0)
            else:
                values.append(0.0)
        if has_data:
            rows.append({"label": label, **{p: v for p, v in zip(periods, values)}})

    result_df = pd.DataFrame(rows)
    return periods, result_df


def parse_three_statement_model(sheets: Dict[str, pd.DataFrame]) -> Dict:
    """
    Parse the CFI Three-Statement Model format.
    Returns a dict with 'income_statement', 'balance_sheet', 'cash_flow',
    'working_capital', 'depreciation', 'debt' sections.
    """
    # Find the main model sheet
    model_sheet = None
    for name, df in sheets.items():
        if "model" in name.lower() or "statement" in name.lower():
            model_sheet = df
            break
    if model_sheet is None:
        model_sheet = list(sheets.values())[-1]  # last sheet

    periods, data = extract_financial_data(model_sheet)
    if data.empty:
        return {"periods": [], "sections": {}}

    # Categorize rows into sections based on label patterns
    sections = {
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow": [],
        "working_capital": [],
        "depreciation": [],
        "debt": [],
    }

    current_section = "income_statement"
    bs_started = False
    cf_started = False
    for _, row in data.iterrows():
        label_lower = row["label"].lower().strip()

        # Section detection — explicit section headers
        if "balance sheet" in label_lower:
            current_section = "balance_sheet"
            bs_started = True
            continue  # Skip header row itself
        elif "cash flow" in label_lower and "statement" in label_lower:
            current_section = "cash_flow"
            cf_started = True
            continue
        elif "working capital" in label_lower and "schedule" in label_lower:
            current_section = "working_capital"
            continue
        elif "depreciation" in label_lower and "schedule" in label_lower:
            current_section = "depreciation"
            continue
        elif "debt" in label_lower and "schedule" in label_lower:
            current_section = "debt"
            continue

        # Auto-detect balance sheet start: if we're in IS section and
        # encounter typical BS-only labels (Cash, Total Assets, etc.)
        if not bs_started and current_section == "income_statement":
            if label_lower in ("cash", "cash and cash equivalents",
                               "cash & equivalents", "total assets",
                               "assets"):
                current_section = "balance_sheet"
                bs_started = True

        # Auto-detect cash flow start: if we're in BS section and
        # encounter "Net Earnings" or "Cash from Operations" again after BS
        if bs_started and not cf_started and current_section == "balance_sheet":
            if label_lower in ("net earnings", "net income") and \
               any(r["label"].lower().strip() in ("net earnings", "net income") for r in sections["income_statement"]):
                current_section = "cash_flow"
                cf_started = True

        # Skip check/header rows
        if label_lower in ["check", "ok", "balance sheet check"]:
            continue
        if "chart" in label_lower and "graph" in label_lower:
            break

        sections[current_section].append(row.to_dict())

    # Convert to DataFrames
    result = {"periods": periods}
    for key, rows in sections.items():
        if rows:
            result[key] = pd.DataFrame(rows)
        else:
            result[key] = pd.DataFrame()

    return result
