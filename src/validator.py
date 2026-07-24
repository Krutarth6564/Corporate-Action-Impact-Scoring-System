from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

class CorporateActionRecord(BaseModel):
    """Pydantic model validating structured corporate action announcement data."""

    filename: str = Field(..., description="Source PDF filename")
    filepath: str = Field(..., description="Source PDF file path")
    ticker: str = Field(default="UNKNOWN", description="NSE/BSE ticker symbol")
    company_name: str = Field(..., description="Full corporate entity name")
    exchange: str = Field(default="NSE/BSE", description="Stock exchange (NSE, BSE, or NSE/BSE)")
    announcement_type: str = Field(..., description="Classified category of announcement")
    
    # Financial & Order Win Details
    order_type: Optional[str] = Field(default="N/A", description="Government or Private order type")
    contract_value_inr_cr: Optional[float] = Field(default=None, description="Contract or event value in INR Crores")
    formatted_contract_value: str = Field(default="N/A", description="Human readable currency format")
    currency: str = Field(default="INR", description="Currency symbol/code")
    client: Optional[str] = Field(default="N/A", description="Client or issuing authority name")
    government_or_private: Optional[str] = Field(default="N/A", description="Classification of client")
    sector: str = Field(default="General Industrials", description="Industry sector classification")
    
    # Execution & Dates
    project_duration: Optional[str] = Field(default="N/A", description="Stated project duration")
    execution_timeline: Optional[str] = Field(default="N/A", description="Execution target timeline")
    revenue_impact: Optional[str] = Field(default="N/A", description="Expected revenue impact statement")
    order_date: Optional[str] = Field(default="N/A", description="Date of order placement")
    filing_date: Optional[str] = Field(default="N/A", description="Date of filing to exchange")
    
    # Litigation & Compliance Triggers
    gst_notice: bool = Field(default=False, description="Flag for GST notice disclosure")
    gst_notice_amount_inr_cr: Optional[float] = Field(default=None, description="GST demand value in Cr")
    penalty: bool = Field(default=False, description="Flag for regulatory penalty")
    penalty_amount_inr_cr: Optional[float] = Field(default=None, description="Penalty value in Cr")
    tax_demand: bool = Field(default=False, description="Flag for tax demand disclosure")
    tax_demand_amount_inr_cr: Optional[float] = Field(default=None, description="Tax demand in Cr")
    court_case: bool = Field(default=False, description="Flag for litigation or court dispute")
    court_case_details: Optional[str] = Field(default="N/A", description="Summary of litigation")
    
    # Signals & Risk Analysis
    keywords: List[str] = Field(default_factory=list, description="Extracted key financial terms")
    positive_signals: List[str] = Field(default_factory=list, description="Key positive catalysts identified")
    negative_signals: List[str] = Field(default_factory=list, description="Key negative concerns identified")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors disclosed")
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")
    
    # Scoring & Summarization Outputs
    summary: str = Field(default="", description="Executive business summary statement")
    impact_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Explainable impact score (0 to 100)")
    impact_rating: str = Field(default="Low", description="Rating category: Very High, High, Medium, Low")
    score_explanation: str = Field(default="", description="Detailed step-by-step scoring rationale")
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Factor score decomposition")
    rank: Optional[int] = Field(default=None, description="Global leaderboard rank position")

    @field_validator("impact_score")
    @classmethod
    def round_impact_score(cls, v: float) -> float:
        return round(min(100.0, max(0.0, v)), 1)
