import pytest
from pathlib import Path
from src.pdf_parser import HybridPDFParser, ParsedPDFDocument
from config.config import RAW_DATA_DIR

def test_pdf_parser():
    parser = HybridPDFParser()
    pdfs = list(RAW_DATA_DIR.glob("*.pdf"))
    if pdfs:
        parsed = parser.parse(pdfs[0])
        assert isinstance(parsed, ParsedPDFDocument)
        assert parsed.page_count >= 1
        assert parsed.filename == pdfs[0].name
