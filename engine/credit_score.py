"""
FAMAS Credit Risk Scoring — Altman Z-Score and Custom Credit Scorecard.
"""
import pandas as pd
from typing import Dict, Optional, List, Tuple
from engine.ratios import RatioEngine, _safe_div


# ── Credit Rating Grades ──────────────────────────────────────────────────────
RATING_GRADES = [
    ("AAA", 95, 100, "#00e676", "Exceptional — Lowest risk. Extremely strong capacity to meet obligations."),
    ("AA",  85,  95, "#00c853", "Very Strong — Very low credit risk. Strong financial position."),
    ("A",   75,  85, "#69f0ae", "Strong — Low credit risk. Adequate financial strength."),
    ("BBB", 65,  75, "#ffeb3b", "Adequate — Moderate credit risk. Satisfactory fundamentals."),
    ("BB",  55,  65, "#ffc107", "Speculative — Elevated risk. Vulnerable to adverse conditions."),
    ("B",   40,  55, "#ff9800", "Highly Speculative — Material credit risk. Weak financial capacity."),
    ("CCC", 25,  40, "#ff5722", "Substantial Risk — Currently vulnerable. Dependent on favorable conditions."),
    ("CC",  15,  25, "#f44336", "Very High Risk — Highly vulnerable to default."),
    ("C",    5,  15, "#d32f2f", "Near Default — Extremely vulnerable. Default is a real possibility."),
    ("D",    0,   5, "#b71c1c", "Default — Payment default or breach of commitment."),
]


def get_rating_grade(score: float) -> Tuple[str, str, str]:
    """Return (grade, color, description) for a given score 0-100."""
    for grade, low, high, color, desc in RATING_GRADES:
        if low <= score <= high:
            return grade, color, desc
    return "NR", "#757575", "Not Rated — Insufficient data for rating."


# ── Altman Z-Score ────────────────────────────────────────────────────────────

class AltmanZScore:
    """
    Calculates the Altman Z-Score for credit risk assessment.
    - Manufacturing: Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5
    - Service:       Z' = 6.56X1 + 3.26X2 + 6.72X3 + 1.05X4
    """

    @staticmethod
    def calculate(
        working_capital: float,
        total_assets: float,
        retained_earnings: float,
        ebit: float,
        market_value_equity: float,  # Can use book value as proxy
        total_liabilities: float,
        revenue: float,
        model: str = "manufacturing"
    ) -> Dict:
        if total_assets == 0:
            return {"z_score": None, "zone": "N/A", "components": {}}

        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = _safe_div(market_value_equity, total_liabilities) or 0

        components = {"X1 (WC/TA)": round(x1, 4), "X2 (RE/TA)": round(x2, 4),
                       "X3 (EBIT/TA)": round(x3, 4), "X4 (Eq/TL)": round(x4, 4)}

        if model == "manufacturing":
            x5 = revenue / total_assets
            components["X5 (Rev/TA)"] = round(x5, 4)
            z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
            zone = "Safe Zone" if z > 2.99 else ("Grey Zone" if z > 1.81 else "Distress Zone")
        else:
            z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
            zone = "Safe Zone" if z > 2.60 else ("Grey Zone" if z > 1.10 else "Distress Zone")

        return {
            "z_score": round(z, 4),
            "zone": zone,
            "model": model,
            "components": components,
        }


# ── Custom Credit Scorecard ───────────────────────────────────────────────────

class CreditScorecard:
    """
    Custom weighted credit scorecard across 5 dimensions.
    Each dimension scores 0-100, weighted to produce final score.
    """

    WEIGHTS = {
        "Profitability": 0.20,
        "Leverage": 0.25,
        "Liquidity": 0.20,
        "Coverage": 0.20,
        "Trend": 0.15,
    }

    @staticmethod
    def _score_profitability(ratio_engine: RatioEngine, period: str) -> Tuple[float, List[str]]:
        """Score profitability metrics 0-100."""
        scores = []
        flags = []

        gm = ratio_engine.gross_margin(period)
        if gm is not None:
            gm_pct = gm * 100
            if gm_pct >= 40: scores.append(100)
            elif gm_pct >= 25: scores.append(75)
            elif gm_pct >= 15: scores.append(50)
            elif gm_pct >= 5: scores.append(25)
            else:
                scores.append(10)
                flags.append("⚠ Gross margin below 5%")

        nm = ratio_engine.net_margin(period)
        if nm is not None:
            nm_pct = nm * 100
            if nm_pct >= 15: scores.append(100)
            elif nm_pct >= 8: scores.append(75)
            elif nm_pct >= 3: scores.append(50)
            elif nm_pct >= 0: scores.append(30)
            else:
                scores.append(5)
                flags.append("🔴 Negative net margin — company is unprofitable")

        roe = ratio_engine.roe(period)
        if roe is not None:
            roe_pct = roe * 100
            if roe_pct >= 20: scores.append(100)
            elif roe_pct >= 12: scores.append(75)
            elif roe_pct >= 5: scores.append(50)
            elif roe_pct >= 0: scores.append(30)
            else:
                scores.append(5)
                flags.append("🔴 Negative ROE")

        avg = sum(scores) / len(scores) if scores else 50
        return avg, flags

    @staticmethod
    def _score_leverage(ratio_engine: RatioEngine, period: str) -> Tuple[float, List[str]]:
        scores = []
        flags = []

        de = ratio_engine.debt_to_equity(period)
        if de is not None:
            if de <= 0.5: scores.append(100)
            elif de <= 1.0: scores.append(80)
            elif de <= 2.0: scores.append(55)
            elif de <= 3.0: scores.append(30)
            else:
                scores.append(10)
                flags.append("🔴 Extremely high leverage (D/E > 3.0x)")

        da = ratio_engine.debt_to_assets(period)
        if da is not None:
            if da <= 0.3: scores.append(100)
            elif da <= 0.5: scores.append(75)
            elif da <= 0.7: scores.append(45)
            else:
                scores.append(15)
                flags.append("⚠ Debt exceeds 70% of assets")

        avg = sum(scores) / len(scores) if scores else 50
        return avg, flags

    @staticmethod
    def _score_liquidity(ratio_engine: RatioEngine, period: str) -> Tuple[float, List[str]]:
        scores = []
        flags = []

        cr = ratio_engine.current_ratio(period)
        if cr is not None:
            if cr >= 2.0: scores.append(100)
            elif cr >= 1.5: scores.append(80)
            elif cr >= 1.0: scores.append(55)
            elif cr >= 0.7: scores.append(25)
            else:
                scores.append(5)
                flags.append("🔴 Current ratio below 0.7x — severe liquidity risk")

        qr = ratio_engine.quick_ratio(period)
        if qr is not None:
            if qr >= 1.5: scores.append(100)
            elif qr >= 1.0: scores.append(80)
            elif qr >= 0.5: scores.append(45)
            else:
                scores.append(10)
                flags.append("⚠ Quick ratio below 0.5x")

        avg = sum(scores) / len(scores) if scores else 50
        return avg, flags

    @staticmethod
    def _score_coverage(ratio_engine: RatioEngine, period: str) -> Tuple[float, List[str]]:
        scores = []
        flags = []

        ic = ratio_engine.interest_coverage(period)
        if ic is not None:
            if ic >= 5.0: scores.append(100)
            elif ic >= 3.0: scores.append(75)
            elif ic >= 1.5: scores.append(45)
            elif ic >= 1.0: scores.append(20)
            else:
                scores.append(5)
                flags.append("🔴 Interest coverage below 1.0x — cannot cover interest payments")

        cf_d = ratio_engine.cf_to_debt(period)
        if cf_d is not None:
            if cf_d >= 0.5: scores.append(100)
            elif cf_d >= 0.3: scores.append(75)
            elif cf_d >= 0.15: scores.append(45)
            else:
                scores.append(15)
                flags.append("⚠ Weak cash flow relative to debt")

        avg = sum(scores) / len(scores) if scores else 50
        return avg, flags

    @staticmethod
    def _score_trend(ratio_engine: RatioEngine, periods: list) -> Tuple[float, List[str]]:
        """Score based on trends in key metrics across periods."""
        if len(periods) < 2:
            return 50, ["ℹ Insufficient periods for trend analysis"]

        scores = []
        flags = []

        # Revenue trend
        rev_latest = ratio_engine._is("Revenue", periods[-1])
        rev_prior = ratio_engine._is("Revenue", periods[-2])
        if rev_prior > 0:
            rev_growth = (rev_latest - rev_prior) / rev_prior
            if rev_growth > 0.10: scores.append(100)
            elif rev_growth > 0.03: scores.append(75)
            elif rev_growth > 0: scores.append(55)
            elif rev_growth > -0.05: scores.append(30)
            else:
                scores.append(10)
                flags.append("⚠ Revenue declining >5%")

        # Net margin trend
        nm_latest = ratio_engine.net_margin(periods[-1])
        nm_prior = ratio_engine.net_margin(periods[-2])
        if nm_latest is not None and nm_prior is not None:
            if nm_latest > nm_prior:
                scores.append(80)
            elif nm_latest == nm_prior:
                scores.append(60)
            else:
                scores.append(30)
                flags.append("⚠ Declining profitability trend")

        avg = sum(scores) / len(scores) if scores else 50
        return avg, flags

    def calculate(self, ratio_engine: RatioEngine, periods: list) -> Dict:
        """Calculate the full credit scorecard."""
        if not periods:
            return {"total_score": 0, "grade": "NR", "dimensions": {}, "flags": []}

        latest = periods[-1]
        all_flags = []
        dimension_scores = {}

        # Profitability
        score, flags = self._score_profitability(ratio_engine, latest)
        dimension_scores["Profitability"] = {"score": round(score, 1), "weight": self.WEIGHTS["Profitability"]}
        all_flags.extend(flags)

        # Leverage
        score, flags = self._score_leverage(ratio_engine, latest)
        dimension_scores["Leverage"] = {"score": round(score, 1), "weight": self.WEIGHTS["Leverage"]}
        all_flags.extend(flags)

        # Liquidity
        score, flags = self._score_liquidity(ratio_engine, latest)
        dimension_scores["Liquidity"] = {"score": round(score, 1), "weight": self.WEIGHTS["Liquidity"]}
        all_flags.extend(flags)

        # Coverage
        score, flags = self._score_coverage(ratio_engine, latest)
        dimension_scores["Coverage"] = {"score": round(score, 1), "weight": self.WEIGHTS["Coverage"]}
        all_flags.extend(flags)

        # Trend
        score, flags = self._score_trend(ratio_engine, periods)
        dimension_scores["Trend"] = {"score": round(score, 1), "weight": self.WEIGHTS["Trend"]}
        all_flags.extend(flags)

        # Weighted total
        total = sum(d["score"] * d["weight"] for d in dimension_scores.values())
        grade, color, description = get_rating_grade(total)

        return {
            "total_score": round(total, 1),
            "grade": grade,
            "grade_color": color,
            "grade_description": description,
            "dimensions": dimension_scores,
            "flags": all_flags,
            "period": latest,
        }
