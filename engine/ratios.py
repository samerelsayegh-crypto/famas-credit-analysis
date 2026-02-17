"""
FAMAS Ratio Calculation Engine — 30+ financial ratios across 5 categories.
"""
import pandas as pd
from typing import Dict, Optional
import math


def _safe_div(numerator: float, denominator: float) -> Optional[float]:
    """Safe division returning None on zero/invalid denominators."""
    if denominator is None or denominator == 0 or math.isnan(denominator):
        return None
    result = numerator / denominator
    return round(result, 4) if abs(result) < 1e10 else None


def _get_val(spread: pd.DataFrame, category: str, period: str) -> float:
    """Get a value from a spread DataFrame by category and period."""
    if spread.empty or period not in spread.columns:
        return 0.0
    match = spread[spread["Category"] == category]
    if match.empty:
        return 0.0
    val = match.iloc[0][period]
    return float(val) if pd.notna(val) else 0.0


class RatioEngine:
    """Calculates 30+ financial ratios from spread financial statements."""

    RATIO_CATEGORIES = {
        "Profitability": [
            ("Gross Profit Margin", "gross_margin", "%"),
            ("EBITDA Margin", "ebitda_margin", "%"),
            ("Operating Margin (EBIT)", "operating_margin", "%"),
            ("Net Profit Margin", "net_margin", "%"),
            ("Return on Assets (ROA)", "roa", "%"),
            ("Return on Equity (ROE)", "roe", "%"),
            ("Return on Invested Capital (ROIC)", "roic", "%"),
        ],
        "Leverage": [
            ("Debt to Equity", "debt_to_equity", "x"),
            ("Debt to Assets", "debt_to_assets", "x"),
            ("Debt to Capital", "debt_to_capital", "x"),
            ("Debt to EBITDA", "debt_to_ebitda", "x"),
            ("Equity Multiplier", "equity_multiplier", "x"),
            ("Long-Term Debt to Equity", "lt_debt_to_equity", "x"),
        ],
        "Liquidity": [
            ("Current Ratio", "current_ratio", "x"),
            ("Quick Ratio", "quick_ratio", "x"),
            ("Cash Ratio", "cash_ratio", "x"),
            ("Net Working Capital", "nwc", "$"),
            ("NWC % of Revenue", "nwc_pct_revenue", "%"),
        ],
        "Activity / Efficiency": [
            ("Accounts Receivable Days", "ar_days", "days"),
            ("Inventory Days", "inventory_days", "days"),
            ("Accounts Payable Days", "ap_days", "days"),
            ("Cash Conversion Cycle", "ccc", "days"),
            ("Total Asset Turnover", "asset_turnover", "x"),
            ("Fixed Asset Turnover", "fixed_asset_turnover", "x"),
        ],
        "Coverage": [
            ("Interest Coverage (EBIT/Int)", "interest_coverage", "x"),
            ("Debt Service Coverage (DSCR)", "dscr", "x"),
            ("Cash Flow to Debt", "cf_to_debt", "x"),
            ("Cash Flow Coverage", "cf_coverage", "x"),
        ],
    }

    def __init__(self, spreads: Dict[str, pd.DataFrame], periods: list):
        self.is_df = spreads.get("income_statement", pd.DataFrame())
        self.bs_df = spreads.get("balance_sheet", pd.DataFrame())
        self.cf_df = spreads.get("cash_flow", pd.DataFrame())
        self.periods = periods

    def _is(self, cat, period):
        return _get_val(self.is_df, cat, period)

    def _bs(self, cat, period):
        return _get_val(self.bs_df, cat, period)

    def _cf(self, cat, period):
        return _get_val(self.cf_df, cat, period)

    # ── Profitability ─────────────────────────────────────────────────────
    def gross_margin(self, p):
        return _safe_div(self._is("Gross Profit", p), self._is("Revenue", p))

    def ebitda_margin(self, p):
        ebit = self._is("EBIT", p)
        da = self._is("Depreciation & Amortization", p)
        ebitda = ebit + abs(da)
        return _safe_div(ebitda, self._is("Revenue", p))

    def operating_margin(self, p):
        return _safe_div(self._is("EBIT", p), self._is("Revenue", p))

    def net_margin(self, p):
        return _safe_div(self._is("Net Income", p), self._is("Revenue", p))

    def roa(self, p):
        return _safe_div(self._is("Net Income", p), self._bs("Total Assets", p))

    def roe(self, p):
        return _safe_div(self._is("Net Income", p), self._bs("Total Equity", p))

    def roic(self, p):
        ebit = self._is("EBIT", p)
        tax_rate = 0.25  # assumed
        nopat = ebit * (1 - tax_rate)
        equity = self._bs("Total Equity", p)
        debt = self._bs("Long-Term Debt", p)
        invested = equity + debt
        return _safe_div(nopat, invested)

    # ── Leverage ──────────────────────────────────────────────────────────
    def debt_to_equity(self, p):
        return _safe_div(self._bs("Total Liabilities", p), self._bs("Total Equity", p))

    def debt_to_assets(self, p):
        return _safe_div(self._bs("Total Liabilities", p), self._bs("Total Assets", p))

    def debt_to_capital(self, p):
        debt = self._bs("Total Liabilities", p)
        equity = self._bs("Total Equity", p)
        return _safe_div(debt, debt + equity)

    def debt_to_ebitda(self, p):
        ebit = self._is("EBIT", p)
        da = self._is("Depreciation & Amortization", p)
        ebitda = ebit + abs(da)
        return _safe_div(self._bs("Long-Term Debt", p), ebitda)

    def equity_multiplier(self, p):
        return _safe_div(self._bs("Total Assets", p), self._bs("Total Equity", p))

    def lt_debt_to_equity(self, p):
        return _safe_div(self._bs("Long-Term Debt", p), self._bs("Total Equity", p))

    # ── Liquidity ─────────────────────────────────────────────────────────
    def current_ratio(self, p):
        return _safe_div(self._bs("Total Current Assets", p), self._bs("Total Current Liabilities", p))

    def quick_ratio(self, p):
        ca = self._bs("Total Current Assets", p)
        inv = self._bs("Inventory", p)
        return _safe_div(ca - inv, self._bs("Total Current Liabilities", p))

    def cash_ratio(self, p):
        return _safe_div(self._bs("Cash & Equivalents", p), self._bs("Total Current Liabilities", p))

    def nwc(self, p):
        return self._bs("Total Current Assets", p) - self._bs("Total Current Liabilities", p)

    def nwc_pct_revenue(self, p):
        nwc_val = self.nwc(p)
        return _safe_div(nwc_val, self._is("Revenue", p))

    # ── Activity / Efficiency ─────────────────────────────────────────────
    def ar_days(self, p):
        return _safe_div(self._bs("Accounts Receivable", p) * 365, self._is("Revenue", p))

    def inventory_days(self, p):
        cogs = abs(self._is("Cost of Goods Sold", p))
        return _safe_div(self._bs("Inventory", p) * 365, cogs) if cogs > 0 else None

    def ap_days(self, p):
        cogs = abs(self._is("Cost of Goods Sold", p))
        return _safe_div(self._bs("Accounts Payable", p) * 365, cogs) if cogs > 0 else None

    def ccc(self, p):
        ar = self.ar_days(p)
        inv = self.inventory_days(p)
        ap = self.ap_days(p)
        if all(v is not None for v in [ar, inv, ap]):
            return round(ar + inv - ap, 2)
        return None

    def asset_turnover(self, p):
        return _safe_div(self._is("Revenue", p), self._bs("Total Assets", p))

    def fixed_asset_turnover(self, p):
        return _safe_div(self._is("Revenue", p), self._bs("PP&E (Net)", p))

    # ── Coverage ──────────────────────────────────────────────────────────
    def interest_coverage(self, p):
        return _safe_div(self._is("EBIT", p), abs(self._is("Interest Expense", p)))

    def dscr(self, p):
        cfo = self._cf("Cash from Operations", p)
        interest = abs(self._is("Interest Expense", p))
        # Simplified DSCR: cash from ops / (interest + principal)
        debt_repay = abs(self._cf("Debt Issuance/(Repayment)", p))
        total_ds = interest + debt_repay
        return _safe_div(cfo, total_ds) if total_ds > 0 else None

    def cf_to_debt(self, p):
        return _safe_div(self._cf("Cash from Operations", p), self._bs("Long-Term Debt", p))

    def cf_coverage(self, p):
        cfo = self._cf("Cash from Operations", p)
        interest = abs(self._is("Interest Expense", p))
        return _safe_div(cfo, interest) if interest > 0 else None

    # ── Master Calculation ────────────────────────────────────────────────
    def calculate_all(self) -> Dict[str, pd.DataFrame]:
        """Calculate all ratios for all periods. Returns dict of category → DataFrame."""
        method_map = {
            "gross_margin": self.gross_margin,
            "ebitda_margin": self.ebitda_margin,
            "operating_margin": self.operating_margin,
            "net_margin": self.net_margin,
            "roa": self.roa,
            "roe": self.roe,
            "roic": self.roic,
            "debt_to_equity": self.debt_to_equity,
            "debt_to_assets": self.debt_to_assets,
            "debt_to_capital": self.debt_to_capital,
            "debt_to_ebitda": self.debt_to_ebitda,
            "equity_multiplier": self.equity_multiplier,
            "lt_debt_to_equity": self.lt_debt_to_equity,
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "cash_ratio": self.cash_ratio,
            "nwc": self.nwc,
            "nwc_pct_revenue": self.nwc_pct_revenue,
            "ar_days": self.ar_days,
            "inventory_days": self.inventory_days,
            "ap_days": self.ap_days,
            "ccc": self.ccc,
            "asset_turnover": self.asset_turnover,
            "fixed_asset_turnover": self.fixed_asset_turnover,
            "interest_coverage": self.interest_coverage,
            "dscr": self.dscr,
            "cf_to_debt": self.cf_to_debt,
            "cf_coverage": self.cf_coverage,
        }

        results = {}
        for category, ratio_defs in self.RATIO_CATEGORIES.items():
            rows = []
            for display_name, method_key, unit in ratio_defs:
                method = method_map.get(method_key)
                if not method:
                    continue
                row = {"Ratio": display_name, "Unit": unit}
                for p in self.periods:
                    val = method(p)
                    if val is not None:
                        if unit == "%":
                            row[p] = round(val * 100, 2)
                        elif unit == "days":
                            row[p] = round(val, 1)
                        elif unit == "$":
                            row[p] = round(val, 0)
                        else:
                            row[p] = round(val, 2)
                    else:
                        row[p] = None
                rows.append(row)
            results[category] = pd.DataFrame(rows)

        return results

    def get_key_metrics(self) -> Dict[str, Dict]:
        """Get the most recent period's key metrics for the dashboard."""
        if not self.periods:
            return {}
        latest = self.periods[-1]
        return {
            "Gross Margin": {"value": self.gross_margin(latest), "format": "%"},
            "Net Margin": {"value": self.net_margin(latest), "format": "%"},
            "ROE": {"value": self.roe(latest), "format": "%"},
            "Current Ratio": {"value": self.current_ratio(latest), "format": "x"},
            "Debt/Equity": {"value": self.debt_to_equity(latest), "format": "x"},
            "Interest Coverage": {"value": self.interest_coverage(latest), "format": "x"},
        }
