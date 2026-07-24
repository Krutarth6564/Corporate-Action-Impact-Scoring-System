from typing import Dict, Any, Tuple
from config.config import load_scoring_config
from src.validator import CorporateActionRecord
from src.logger import get_logger

logger = get_logger("Scorer")

class ExplainableImpactScorer:
    """Production Explainable Impact Scoring Engine powered by configurable YAML weights."""

    def __init__(self):
        self.config = load_scoring_config()
        self.category_weights = self.config.get("category_weights", {})
        self.thresholds = self.config.get("financial_scale_thresholds", {})
        self.sector_multipliers = self.config.get("sector_sensitivity_multipliers", {})
        self.signal_weights = self.config.get("signal_weights", {})
        self.rating_thresholds = self.config.get("rating_thresholds", {})

    def score(self, record: CorporateActionRecord) -> CorporateActionRecord:
        """Calculates an explainable 0-100 Impact Score, Rating Tag, and step-by-step Explanation."""
        # 1. Base Category Severity (Max 45)
        cat_score = self.category_weights.get(record.announcement_type, 15.0)

        # 2. Order Size & Financial Magnitude (Max 30)
        mag_score = self._calculate_magnitude_score(record.contract_value_inr_cr, record.announcement_type)

        # 3. Sector Sensitivity Multiplier (1.0 to 1.25x)
        sector_multiplier = self.sector_multipliers.get(record.sector, 1.0)

        # 4. Signals & Risk Factors Impact (+/- 15)
        signal_score = 0.0
        if record.positive_signals:
            signal_score += len(record.positive_signals) * self.signal_weights.get("positive_signal_bonus", 5.0)
        if record.negative_signals:
            signal_score -= len(record.negative_signals) * self.signal_weights.get("negative_signal_penalty", 8.0)
        if record.risk_factors:
            signal_score -= len(record.risk_factors) * self.signal_weights.get("risk_factor_penalty", 6.0)

        # 5. Government Client / Credibility Bonus (+5)
        credibility_score = 0.0
        if record.government_or_private == "Government":
            credibility_score += self.signal_weights.get("government_order_bonus", 5.0)

        # Subtotal Calculation
        subtotal = (cat_score + mag_score + signal_score + credibility_score) * sector_multiplier
        final_score = round(min(100.0, max(0.0, subtotal)), 1)

        # Assign 4-Tier Rating
        rating = self._determine_rating(final_score)

        # Score Breakdown Dictionary
        breakdown = {
            "Category Base Weight": cat_score,
            "Financial Magnitude": mag_score,
            "Sector Multiplier": sector_multiplier,
            "Signals & Risk Adjustment": signal_score,
            "Credibility Bonus": credibility_score
        }

        # Generate Explainable Rationale
        explanation = self._generate_explanation(record, final_score, rating, breakdown)

        # Update and return validated record
        record.impact_score = final_score
        record.impact_rating = rating
        record.score_explanation = explanation
        record.score_breakdown = breakdown

        return record

    def _calculate_magnitude_score(self, val_cr: float | None, category: str) -> float:
        if val_cr is not None:
            if val_cr >= self.thresholds.get("very_large_cr", 5000.0):
                return 30.0
            elif val_cr >= self.thresholds.get("large_cr", 1000.0):
                return 25.0
            elif val_cr >= self.thresholds.get("medium_cr", 250.0):
                return 20.0
            elif val_cr >= self.thresholds.get("small_cr", 50.0):
                return 15.0
            elif val_cr > 0:
                return 10.0

        if category in ["Debt Default & Downgrade", "Litigation & Court Case", "Merger & Acquisition"]:
            return 20.0
        elif category in ["Financial Results", "Order Win", "GST Notice"]:
            return 15.0
        return 8.0

    def _determine_rating(self, score: float) -> str:
        vh = self.rating_thresholds.get("very_high", 85.0)
        h = self.rating_thresholds.get("high", 70.0)
        m = self.rating_thresholds.get("medium", 45.0)

        if score >= vh:
            return "Very High"
        elif score >= h:
            return "High"
        elif score >= m:
            return "Medium"
        else:
            return "Low"

    def _generate_explanation(
        self, record: CorporateActionRecord, score: float, rating: str, breakdown: Dict[str, float]
    ) -> str:
        parts = [
            f"Assigned an explainable Impact Score of {score}/100 ({rating} Rating) for {record.company_name} ({record.ticker}).",
            f"Category '{record.announcement_type}' contributed {breakdown['Category Base Weight']} base points.",
        ]
        if record.contract_value_inr_cr:
            parts.append(f"Disclosed contract/event magnitude of {record.formatted_contract_value} contributed {breakdown['Financial Magnitude']} magnitude points.")
        if breakdown['Sector Multiplier'] > 1.0:
            parts.append(f"Sector '{record.sector}' applied a {breakdown['Sector Multiplier']}x sensitivity multiplier.")
        if record.government_or_private == "Government":
            parts.append("Government client status added a +5.0 credibility bonus.")
        if record.risk_factors or record.negative_signals:
            parts.append(f"Disclosed risk factors / negative concerns adjusted score by {breakdown['Signals & Risk Adjustment']} points.")

        return " ".join(parts)
