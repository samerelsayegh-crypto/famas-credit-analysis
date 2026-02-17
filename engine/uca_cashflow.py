"""
FAMAS UCA Cash Flow Statement — Uniform Credit Analysis cash flow format.
"""
import pandas as pd
from typing import Dict, List
from engine.ratios import _get_val


class UCACashFlow:
    """
    Builds the Uniform Credit Analysis (UCA) Cash Flow statement.
    The UCA format focuses on a borrower's ability to generate cash
    from its core operations to service debt.
    """

    def __init__(self, spreads: Dict[str, pd.DataFrame], periods: list):
        self.is_df = spreads.get("income_statement", pd.DataFrame())
        self.bs_df = spreads.get("balance_sheet", pd.DataFrame())
        self.cf_df = spreads.get("cash_flow", pd.DataFrame())
        self.periods = periods

    def _is(self, cat, p):
        return _get_val(self.is_df, cat, p)

    def _bs(self, cat, p):
        return _get_val(self.bs_df, cat, p)

    def _cf(self, cat, p):
        return _get_val(self.cf_df, cat, p)

    def _bs_prev(self, cat, p_idx):
        """Get prior period balance sheet value."""
        if p_idx <= 0:
            return 0.0
        return _get_val(self.bs_df, cat, self.periods[p_idx - 1])

    def build(self) -> pd.DataFrame:
        """Build the full UCA Cash Flow statement."""
        rows = []

        for i, p in enumerate(self.periods):
            revenue = self._is("Revenue", p)
            cogs = abs(self._is("Cost of Goods Sold", p))
            gross_profit = self._is("Gross Profit", p)
            opex = abs(self._is("Total Operating Expenses", p))
            ebit = self._is("EBIT", p)
            interest = abs(self._is("Interest Expense", p))
            tax = abs(self._is("Income Tax", p))
            net_income = self._is("Net Income", p)
            da = abs(self._is("Depreciation & Amortization", p))

            # Working capital changes
            ar_change = self._bs("Accounts Receivable", p) - self._bs_prev("Accounts Receivable", i)
            inv_change = self._bs("Inventory", p) - self._bs_prev("Inventory", i)
            ap_change = self._bs("Accounts Payable", p) - self._bs_prev("Accounts Payable", i)

            # UCA sections
            cash_from_sales = revenue - ar_change
            cash_cogs = cogs + inv_change - ap_change
            cash_gross_profit = cash_from_sales - cash_cogs
            cash_opex = opex - da  # Remove non-cash from opex
            cash_after_operations = cash_gross_profit - cash_opex - tax
            cash_after_debt_service = cash_after_operations - interest

            # Financing
            capex = abs(self._cf("Capital Expenditures", p))
            debt_change = self._cf("Debt Issuance/(Repayment)", p)
            equity_change = self._cf("Equity Issuance/(Repayment)", p)
            financing_surplus = cash_after_debt_service - capex + debt_change + equity_change

            rows.append({
                "period": p,
                "Net Sales / Revenue": revenue,
                "(-) Change in AR": -ar_change,
                "= Cash from Sales": cash_from_sales,
                "(-) Cash Cost of Goods Sold": -cash_cogs,
                "= Cash Gross Profit": cash_gross_profit,
                "(-) Cash Operating Expenses": -cash_opex,
                "(-) Income Tax": -tax,
                "= Cash After Operations": cash_after_operations,
                "(-) Interest Expense": -interest,
                "= Cash After Debt Service": cash_after_debt_service,
                "(-) Capital Expenditures": -capex,
                "(+/-) Debt Issuance/Repayment": debt_change,
                "(+/-) Equity Issuance/Repayment": equity_change,
                "= Financing Surplus / (Deficit)": financing_surplus,
            })

        uca_df = pd.DataFrame(rows)
        return uca_df

    def get_summary_metrics(self) -> Dict[str, Dict]:
        """Get UCA summary metrics for the latest period."""
        if not self.periods:
            return {}

        uca = self.build()
        if uca.empty:
            return {}

        latest = uca.iloc[-1]
        return {
            "Cash from Sales": latest.get("= Cash from Sales", 0),
            "Cash After Operations": latest.get("= Cash After Operations", 0),
            "Cash After Debt Service": latest.get("= Cash After Debt Service", 0),
            "Financing Surplus/(Deficit)": latest.get("= Financing Surplus / (Deficit)", 0),
        }
