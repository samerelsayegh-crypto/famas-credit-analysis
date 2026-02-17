"""
FAMAS Spreading Engine — Standardizes financial statements into FAMAS categories
with common-size analysis.
"""
import pandas as pd
from typing import Dict, List, Optional


# ── Standard FAMAS Line-Item Categories ───────────────────────────────────────

INCOME_STATEMENT_MAP = {
    # Revenue
    "revenue": "Revenue",
    "total net revenue": "Revenue",
    "total revenue": "Revenue",
    "net revenue": "Revenue",
    "net sales": "Revenue",
    "sales": "Revenue",
    "revenue stream": "Revenue",

    # COGS
    "cost of goods sold": "Cost of Goods Sold",
    "cost of goods sold (cogs)": "Cost of Goods Sold",
    "cogs": "Cost of Goods Sold",
    "cost of sales": "Cost of Goods Sold",
    "cost of revenue": "Cost of Goods Sold",

    # Gross Profit
    "gross profit": "Gross Profit",
    "gross margin": "Gross Profit",

    # Salaries
    "salaries": "Salaries & Benefits",
    "salaries and benefits": "Salaries & Benefits",
    "salaries, benefits & wages": "Salaries & Benefits",
    "compensation": "Salaries & Benefits",

    # Rent
    "rent": "Rent & Overhead",
    "rent and overhead": "Rent & Overhead",
    "occupancy": "Rent & Overhead",

    # D&A
    "depreciation & amortization": "Depreciation & Amortization",
    "depreciation and amortization": "Depreciation & Amortization",
    "depreciation": "Depreciation & Amortization",
    "amortization": "Depreciation & Amortization",

    # Other OpEx
    "advertising & promotion": "Other Operating Expenses",
    "insurance": "Other Operating Expenses",
    "maintenance": "Other Operating Expenses",
    "office supplies": "Other Operating Expenses",
    "telecommunication": "Other Operating Expenses",
    "travel": "Other Operating Expenses",
    "utilities": "Other Operating Expenses",
    "other expense": "Other Operating Expenses",
    "total expenses": "Total Operating Expenses",

    # EBIT
    "earnings before interest & taxes": "EBIT",
    "ebit": "EBIT",
    "operating income": "EBIT",
    "operating profit": "EBIT",

    # Interest
    "interest expense": "Interest Expense",
    "interest": "Interest Expense",
    "interest expense ($)": "Interest Expense",

    # EBT
    "earnings before taxes": "EBT",
    "earnings before tax": "EBT",
    "income before tax": "EBT",
    "ebt": "EBT",

    # Tax
    "income tax": "Income Tax",
    "income tax expense": "Income Tax",
    "tax expense": "Income Tax",
    "taxes": "Income Tax",

    # Net Income
    "net income": "Net Income",
    "net earnings": "Net Income",
    "net profit": "Net Income",
    "net income (loss)": "Net Income",

    # EBITDA (often derived, but may appear)
    "ebitda": "EBITDA",
}

BALANCE_SHEET_MAP = {
    # Current Assets
    "cash": "Cash & Equivalents",
    "cash and cash equivalents": "Cash & Equivalents",
    "cash & equivalents": "Cash & Equivalents",
    "accounts receivable": "Accounts Receivable",
    "trade receivables": "Accounts Receivable",
    "inventory": "Inventory",
    "inventories": "Inventory",
    "prepaid expenses": "Prepaid Expenses",
    "prepaid": "Prepaid Expenses",
    "other current assets": "Other Current Assets",
    "total current assets": "Total Current Assets",
    "current assets": "Total Current Assets",

    # Non-Current Assets
    "property, plant & equipment": "PP&E (Net)",
    "property, plant and equipment": "PP&E (Net)",
    "property & equipment": "PP&E (Net)",
    "ppe closing": "PP&E (Net)",
    "pp&e": "PP&E (Net)",
    "net pp&e": "PP&E (Net)",
    "intangible assets": "Intangible Assets",
    "goodwill": "Goodwill",
    "other non-current assets": "Other Non-Current Assets",
    "total assets": "Total Assets",

    # Current Liabilities
    "accounts payable": "Accounts Payable",
    "trade payables": "Accounts Payable",
    "accrued liabilities": "Accrued Liabilities",
    "accrued expenses": "Accrued Liabilities",
    "short-term debt": "Short-Term Debt",
    "current portion of long-term debt": "Current Portion of LT Debt",
    "other current liabilities": "Other Current Liabilities",
    "total current liabilities": "Total Current Liabilities",
    "current liabilities": "Total Current Liabilities",

    # Non-Current Liabilities
    "long-term debt": "Long-Term Debt",
    "debt closing": "Long-Term Debt",
    "debt": "Long-Term Debt",
    "notes payable": "Long-Term Debt",
    "other non-current liabilities": "Other Non-Current Liabilities",
    "total liabilities": "Total Liabilities",

    # Equity
    "common stock": "Common Equity",
    "common shares": "Common Equity",
    "share capital": "Common Equity",
    "equity capital": "Common Equity",
    "paid-in capital": "Additional Paid-In Capital",
    "additional paid-in capital": "Additional Paid-In Capital",
    "retained earnings": "Retained Earnings",
    "total shareholder's equity": "Total Equity",
    "shareholder's equity": "Total Equity",
    "total shareholders equity": "Total Equity",
    "total equity": "Total Equity",
    "shareholders equity": "Total Equity",
    "total liabilities & shareholder's equity": "Total Liabilities & Equity",
    "total liabilities and equity": "Total Liabilities & Equity",
}

CASH_FLOW_MAP = {
    "net earnings": "Net Income",
    "net income": "Net Income",
    "depreciation & amortization": "Depreciation & Amortization",
    "plus: depreciation & amortization": "Depreciation & Amortization",
    "changes in working capital": "Changes in Working Capital",
    "less: changes in working capital": "Changes in Working Capital",
    "cash from operations": "Cash from Operations",
    "operating cash flow": "Cash from Operations",

    "investments in property & equipment": "Capital Expenditures",
    "capital expenditures": "Capital Expenditures",
    "capex": "Capital Expenditures",
    "cash from investing": "Cash from Investing",

    "issuance (repayment) of debt": "Debt Issuance/(Repayment)",
    "issuance (repayment) of equity": "Equity Issuance/(Repayment)",
    "cash from financing": "Cash from Financing",

    "net increase (decrease) in cash": "Net Change in Cash",
    "net change in cash": "Net Change in Cash",
    "opening cash balance": "Opening Cash Balance",
    "closing cash balance": "Closing Cash Balance",
}


def _match_label(raw_label: str, mapping: Dict[str, str]) -> Optional[str]:
    """Match a raw label to a standardized category."""
    clean = raw_label.lower().strip()
    # Direct match
    if clean in mapping:
        return mapping[clean]
    # Partial match
    for key, standard in mapping.items():
        if key in clean or clean in key:
            return standard
    return None


class SpreadEngine:
    """Standardizes raw financial data into FAMAS-format spreading."""

    def __init__(self, parsed_data: Dict):
        self.parsed = parsed_data
        self.periods = parsed_data.get("periods", [])

    def spread_income_statement(self) -> pd.DataFrame:
        """Spread the income statement into standardized categories."""
        raw = self.parsed.get("income_statement", pd.DataFrame())
        if raw.empty:
            return pd.DataFrame()
        return self._spread_section(raw, INCOME_STATEMENT_MAP, "Revenue")

    def spread_balance_sheet(self) -> pd.DataFrame:
        """Spread the balance sheet into standardized categories."""
        raw = self.parsed.get("balance_sheet", pd.DataFrame())
        if raw.empty:
            return pd.DataFrame()
        return self._spread_section(raw, BALANCE_SHEET_MAP, "Total Assets")

    def spread_cash_flow(self) -> pd.DataFrame:
        """Spread the cash flow statement into standardized categories."""
        raw = self.parsed.get("cash_flow", pd.DataFrame())
        if raw.empty:
            return pd.DataFrame()
        return self._spread_section(raw, CASH_FLOW_MAP, None)

    def _spread_section(self, raw_df: pd.DataFrame, mapping: Dict, base_item: Optional[str]) -> pd.DataFrame:
        """Generic spreading logic with common-size calculation."""
        rows = []
        for _, row in raw_df.iterrows():
            label = row.get("label", "")
            standard = _match_label(label, mapping)
            if standard is None:
                standard = label  # Keep original if no mapping

            entry = {"Category": standard, "Original Label": label}
            for p in self.periods:
                val = row.get(p, 0.0)
                entry[p] = val
            rows.append(entry)

        if not rows:
            return pd.DataFrame()

        result = pd.DataFrame(rows)

        # Consolidate duplicate categories (sum them)
        numeric_cols = [c for c in result.columns if c not in ("Category", "Original Label")]
        result = result.groupby("Category", sort=False).agg(
            {**{c: "sum" for c in numeric_cols}, "Original Label": "first"}
        ).reset_index()

        # Common-size analysis
        if base_item and base_item in result["Category"].values:
            base_row = result[result["Category"] == base_item].iloc[0]
            for p in self.periods:
                base_val = base_row[p]
                cs_col = f"{p} %"
                if base_val != 0:
                    result[cs_col] = (result[p] / base_val * 100).round(2)
                else:
                    result[cs_col] = 0.0

        return result

    def get_all_spreads(self) -> Dict[str, pd.DataFrame]:
        """Return all three spread statements."""
        return {
            "income_statement": self.spread_income_statement(),
            "balance_sheet": self.spread_balance_sheet(),
            "cash_flow": self.spread_cash_flow(),
        }
