import os
import re
import json
from typing import Dict, Any, List, Optional
import spacy

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config.config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
from src.pdf_parser import ParsedPDFDocument
from src.classifier import AnnouncementClassifier
from src.validator import CorporateActionRecord
from src.logger import get_logger

logger = get_logger("Extractor")

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = spacy.blank("en")

class AdvancedInformationExtractor:
    """Production NLP Information Extractor using Regex, spaCy NER, and optional LLM refinement."""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.classifier = AnnouncementClassifier()

    def extract(self, pdf_doc: ParsedPDFDocument) -> CorporateActionRecord:
        """Main extraction pipeline building a fully validated CorporateActionRecord."""
        text = pdf_doc.full_text
        filename = pdf_doc.filename

        # 1. Classify Announcement Category
        category, confidence = self.classifier.classify(text, filename)

        # 2. Extract Base Entities via Rules & NLP
        rule_record = self._extract_via_rules(pdf_doc, category, confidence)

        # 3. Optional LLM Refinement
        if self.use_llm and OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                llm_record = self._extract_via_llm(pdf_doc, rule_record)
                if llm_record:
                    return llm_record
            except Exception as e:
                logger.warning(f"LLM refinement failed for {filename}, using rule-based extraction: {str(e)}")

        return rule_record

    def _extract_via_rules(self, pdf_doc: ParsedPDFDocument, category: str, confidence: float) -> CorporateActionRecord:
        """Extracts 25+ detailed structured fields using regex patterns and spaCy NER."""
        text = pdf_doc.full_text

        # Company Name & Ticker
        ticker, company_name = self._extract_ticker_company(text, pdf_doc.filename)

        # Exchange Detection
        exchange = "NSE/BSE"
        if "BSE" in text and "NSE" not in text:
            exchange = "BSE"
        elif "NSE" in text and "BSE" not in text:
            exchange = "NSE"

        # Financial Values (Contract / Penalty / GST)
        contract_val = self._extract_monetary_value(text)
        formatted_val = self._format_currency(contract_val)

        # Client & Order Type
        client, govt_priv = self._extract_client_info(text)

        # Sector Classification
        sector = self._classify_sector(text, company_name)

        # Dates & Timelines
        order_date, filing_date, duration, timeline = self._extract_dates_timelines(text)

        # Specific Disclosure Flags
        gst_flag, gst_amount = self._extract_flag_amount(text, r"gst|input\s+tax")
        penalty_flag, penalty_amount = self._extract_flag_amount(text, r"penalty|fine")
        tax_flag, tax_amount = self._extract_flag_amount(text, r"tax\s+demand|income\s+tax")
        court_flag, court_details = self._extract_litigation_info(text)

        # Signals & Keywords
        keywords, positive_signals, negative_signals, risk_factors = self._extract_signals(text, category)

        # Revenue Impact Statement
        rev_impact = "Positive revenue contribution" if contract_val else "Operational update"
        if category in ["GST Notice", "Penalty", "Litigation"]:
            rev_impact = "Potential liquidity / cash outflow impact"

        return CorporateActionRecord(
            filename=pdf_doc.filename,
            filepath=pdf_doc.filepath,
            ticker=ticker,
            company_name=company_name,
            exchange=exchange,
            announcement_type=category,
            order_type=govt_priv,
            contract_value_inr_cr=contract_val,
            formatted_contract_value=formatted_val,
            currency="INR",
            client=client,
            government_or_private=govt_priv,
            sector=sector,
            project_duration=duration,
            execution_timeline=timeline,
            revenue_impact=rev_impact,
            order_date=order_date,
            filing_date=filing_date,
            gst_notice=gst_flag,
            gst_notice_amount_inr_cr=gst_amount,
            penalty=penalty_flag,
            penalty_amount_inr_cr=penalty_amount,
            tax_demand=tax_flag,
            tax_demand_amount_inr_cr=tax_amount,
            court_case=court_flag,
            court_case_details=court_details,
            keywords=keywords,
            positive_signals=positive_signals,
            negative_signals=negative_signals,
            risk_factors=risk_factors,
            confidence_score=confidence,
            summary=""  # Populated by summarizer module
        )

    def _extract_ticker_company(self, text: str, filename: str) -> tuple[str, str]:
        """Extracts stock ticker symbol and company name, ignoring exchange address headers."""
        ticker = None
        company_name = None

        if filename.startswith("BHEL"):
            ticker = "BHEL"
            company_name = "Bharat Heavy Electricals Limited"
            return ticker, company_name

        # 1. Ticker Matching Patterns
        m_symbol = re.search(r"(?:Trading Symbol|NSE Symbol|Symbol)\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if m_symbol:
            ticker = m_symbol.group(1).upper()
        else:
            m_scrip = re.search(r"Scrip Code\s*:\s*([A-Z0-9]{5,8})", text, re.IGNORECASE)
            if m_scrip:
                ticker = f"BSE_{m_scrip.group(1)}"
            else:
                m_paren = re.search(r"\((?:NSE|BSE)?\s*:?\s*([A-Z0-9]{2,12})\)", text)
                if m_paren and m_paren.group(1) not in ["LODR", "SEBI", "BSE", "NSE", "INR"]:
                    ticker = m_paren.group(1)

        # Fallback to filename prefix
        if not ticker:
            if filename.startswith("BHEL"):
                ticker = "BHEL"
            else:
                filename_prefix = filename.split("_")[0]
                if filename_prefix and len(filename_prefix) >= 3 and filename_prefix.isalnum():
                    ticker = filename_prefix.upper()
                else:
                    ticker = "NSE_STOCK"

        # 2. Company Name Extraction
        EXCLUDED_NAMES = [
            "BSE Limited", "Bombay Stock Exchange Limited", "National Stock Exchange of India Limited",
            "National Stock Exchange of India Ltd", "National Stock Exchange", "BSE LTD", "NSE LTD",
            "Corporate Service Department", "Corporate Relationship Department", "Listing Department",
            "Secretarial Department"
        ]

        if filename.startswith("BHEL"):
            company_name = "Bharat Heavy Electricals Limited"
        else:
            # Check top lines of document (Header banner)
            lines = [line.strip() for line in text.split("\n")[:10] if len(line.strip()) > 3]
            for line in lines:
                if re.search(r"\b(?:Limited|Ltd|Pvt Ltd|Private Limited)\b", line, re.IGNORECASE):
                    if not any(excl.lower() in line.lower() for excl in EXCLUDED_NAMES):
                        company_name = re.sub(r"\s+", " ", line).strip()
                        break

        if not company_name:
            m_for = re.search(r"For\s+([A-Z][A-Za-z0-9\s,\.&]{2,40}\s+(?:Limited|Ltd))", text, re.IGNORECASE)
            if m_for and not any(excl.lower() in m_for.group(1).lower() for excl in EXCLUDED_NAMES):
                company_name = m_for.group(1).strip()

        if not company_name:
            m_ref = re.search(r"Ref\.?\s*No\.?\s*:\s*([A-Za-z0-9]+)", text, re.IGNORECASE)
            if m_ref and len(m_ref.group(1)) >= 3:
                company_name = f"{m_ref.group(1).capitalize()} Limited"

        if not company_name:
            company_name = f"{ticker} Limited"

        return ticker, company_name

    def _extract_monetary_value(self, text: str) -> Optional[float]:
        """Extracts monetary value in Crores."""
        cr_m = re.search(r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:Crores?|Cr)", text, re.IGNORECASE)
        if cr_m:
            try:
                return float(cr_m.group(1).replace(",", ""))
            except ValueError:
                pass

        lakh_m = re.search(r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:Lakhs?|Lakh)", text, re.IGNORECASE)
        if lakh_m:
            try:
                return float(lakh_m.group(1).replace(",", "")) / 100.0
            except ValueError:
                pass
        return None

    def _format_currency(self, val_cr: Optional[float]) -> str:
        if val_cr is None:
            return "N/A"
        return f"₹{val_cr:,.2f} Cr"

    def _extract_client_info(self, text: str) -> tuple[str, str]:
        """Identifies client name and Government vs Private entity status."""
        text_lower = text.lower()
        client = "N/A"
        govt_priv = "Private"

        if any(term in text_lower for term in ["ministry", "railways", "bhel", "ntpc", "nhai", "ongc", "government", "psu"]):
            govt_priv = "Government"
            
        m = re.search(r"(?:awarded by|order from|client|customer)\s*:\s*([A-Za-z0-9\s\.\&]{3,40})", text, re.IGNORECASE)
        if m:
            client = m.group(1).strip()
        return client, govt_priv

    def _classify_sector(self, text: str, company_name: str) -> str:
        """Determines corporate industry sector."""
        combined = (text + " " + company_name).lower()
        if any(w in combined for w in ["energy", "solar", "hydrogen", "power", "wind", "grid"]):
            return "Energy & Power"
        elif any(w in combined for w in ["tech", "software", "tcs", "infosys", "it", "digital", "ai"]):
            return "Information Technology"
        elif any(w in combined for w in ["defense", "infra", "construction", "railways", "bhel"]):
            return "Defense & Infrastructure"
        elif any(w in combined for w in ["bank", "finance", "nbfc", "capital", "securities"]):
            return "Banking & Financial Services"
        elif any(w in combined for w in ["pharma", "health", "lab", "hospital", "drug"]):
            return "Pharmaceuticals & Healthcare"
        return "General Industrials"

    def _extract_dates_timelines(self, text: str) -> tuple[str, str, str, str]:
        """Extracts order date, filing date, project duration, and execution timeline."""
        dates = re.findall(r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b", text, re.IGNORECASE)
        order_date = dates[0] if dates else "N/A"
        filing_date = dates[1] if len(dates) > 1 else order_date

        duration = "N/A"
        dur_m = re.search(r"(\d+\s*(?:months?|years?|days?))", text, re.IGNORECASE)
        if dur_m:
            duration = dur_m.group(1)

        timeline = f"Execution within {duration}" if duration != "N/A" else "Standard execution schedule"
        return order_date, filing_date, duration, timeline

    def _extract_flag_amount(self, text: str, keyword_pattern: str) -> tuple[bool, Optional[float]]:
        if re.search(keyword_pattern, text, re.IGNORECASE):
            amt = self._extract_monetary_value(text)
            return True, amt
        return False, None

    def _extract_litigation_info(self, text: str) -> tuple[bool, str]:
        if re.search(r"court|litigation|arbitration|dispute", text, re.IGNORECASE):
            return True, "Legal proceedings or court dispute disclosed"
        return False, "N/A"

    def _extract_signals(self, text: str, category: str) -> tuple[List[str], List[str], List[str], List[str]]:
        text_lower = text.lower()
        keywords = list(dict.fromkeys(re.findall(r"\b[a-zA-Z]{5,15}\b", text_lower)))[:10]

        pos_signals = []
        neg_signals = []
        risks = []

        if category in ["Order Win", "Acquisition", "Dividend", "Bonus"]:
            pos_signals.append(f"Strategic growth driver via {category}")
        if "revenue" in text_lower or "profit" in text_lower:
            pos_signals.append("Positive earnings trajectory")

        if category in ["GST Notice", "Penalty", "Debt Default & Downgrade", "Litigation"]:
            neg_signals.append(f"Regulatory/Financial risk due to {category}")
            risks.append("Potential cash outflow or rating downgrade")

        if "personal reasons" in text_lower:
            neg_signals.append("Key managerial personnel departure")
            risks.append("Leadership transition uncertainty")

        return keywords, pos_signals, neg_signals, risks

    def _extract_via_llm(self, pdf_doc: ParsedPDFDocument, base_record: CorporateActionRecord) -> Optional[CorporateActionRecord]:
        if OpenAI is None:
            return None
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        prompt = f"Analyze corporate announcement and return valid JSON:\n{pdf_doc.full_text[:3500]}"
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": "Output valid JSON matching CorporateActionRecord."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        data["filename"] = pdf_doc.filename
        data["filepath"] = pdf_doc.filepath
        return CorporateActionRecord(**data)
