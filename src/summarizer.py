from typing import Optional
from config.config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
from src.validator import CorporateActionRecord
from src.logger import get_logger

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = get_logger("Summarizer")

class BusinessSummarizer:
    """Generates concise, human-readable executive business summaries."""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def generate_summary(self, record: CorporateActionRecord, full_text: str = "") -> str:
        """Generates a 1-2 sentence business summary with rule-based or LLM synthesis."""
        if self.use_llm and OpenAI is not None and OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                llm_summary = self._generate_llm_summary(record, full_text)
                if llm_summary:
                    return llm_summary
            except Exception as e:
                logger.warning(f"LLM summary generation failed for {record.filename}: {str(e)}")

        return self._generate_rule_summary(record)

    def _generate_rule_summary(self, record: CorporateActionRecord) -> str:
        """Rule-based natural language template summary generator."""
        company = record.company_name or record.ticker
        value_str = record.formatted_contract_value if record.formatted_contract_value != "N/A" else ""
        category = record.announcement_type
        rating = record.impact_rating

        if category == "Order Win":
            client_str = f" {record.government_or_private.lower()}" if record.government_or_private != "N/A" else ""
            val_clause = f" of {value_str}" if value_str else ""
            return f"{company} secured a{client_str} order{val_clause} expected to positively impact future revenues. Overall market impact is {rating}."

        elif category in ["GST Notice", "Penalty", "Tax Demand"]:
            val_clause = f" of {value_str}" if value_str else ""
            return f"{company} received a regulatory {category}{val_clause}, signaling potential short-term tax/liquidity liability. Overall market impact is {rating}."

        elif category in ["Debt Default & Downgrade"]:
            return f"{company} disclosed a credit rating downgrade or debt payment default{(' of ' + value_str) if value_str else ''}, reflecting critical solvency risk. Overall market impact is {rating}."

        elif category in ["Dividend", "Buyback", "Bonus", "Stock Split"]:
            return f"{company} announced a corporate capital action ({category}){(' valued at ' + value_str) if value_str else ''} enhancing shareholder value. Overall market impact is {rating}."

        elif category in ["Merger", "Acquisition"]:
            return f"{company} announced a strategic {category}{(' valued at ' + value_str) if value_str else ''} expanding market operations. Overall market impact is {rating}."

        return f"{company} disclosed a corporate regulatory filing regarding {category}. Overall market impact is {rating}."

    def _generate_llm_summary(self, record: CorporateActionRecord, full_text: str) -> Optional[str]:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        prompt = f"Summarize in 1-2 business sentences with rating statement:\nCompany: {record.company_name}\nCategory: {record.announcement_type}\nValue: {record.formatted_contract_value}\nRating: {record.impact_rating}\nText snippet: {full_text[:1500]}"
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
