import pytest
from src.validator import CorporateActionRecord
from src.scorer import ExplainableImpactScorer

def test_explainable_impact_scorer():
    scorer = ExplainableImpactScorer()
    record = CorporateActionRecord(
        filename="BHEL_Order.pdf",
        filepath="/tmp/BHEL_Order.pdf",
        ticker="BHEL",
        company_name="Bharat Heavy Electricals Limited",
        exchange="NSE",
        announcement_type="Order Win",
        contract_value_inr_cr=620.0,
        formatted_contract_value="₹620.00 Cr",
        sector="Defense & Infrastructure",
        government_or_private="Government",
        positive_signals=["Strategic order win"],
        confidence_score=0.95
    )

    scored = scorer.score(record)
    assert scored.impact_score > 50.0
    assert scored.impact_rating in ["Very High", "High", "Medium"]
    assert "Bharat Heavy Electricals Limited" in scored.score_explanation
