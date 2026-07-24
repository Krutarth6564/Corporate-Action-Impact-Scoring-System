import pytest
from src.extractor import AdvancedInformationExtractor
from src.pdf_parser import ParsedPDFDocument

def test_information_extractor():
    extractor = AdvancedInformationExtractor(use_llm=False)
    doc = ParsedPDFDocument(
        filepath="sample.pdf",
        filename="BHEL_Order_Win.pdf",
        page_count=1,
        full_text="Bharat Heavy Electricals Limited (BHEL) secured a government order from NTPC of INR 620 Crores."
    )
    record = extractor.extract(doc)
    assert record.ticker == "BHEL"
    assert record.company_name == "Bharat Heavy Electricals Limited"
    assert record.contract_value_inr_cr == 620.0
    assert record.government_or_private == "Government"
