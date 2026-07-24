import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

import pdfplumber

# Optional OCR dependencies
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from src.logger import get_logger

logger = get_logger("PDFParser")

@dataclass
class ParsedPDFDocument:
    filepath: str
    filename: str
    page_count: int
    full_text: str
    pages_text: List[str] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_scanned: bool = False
    is_corrupted: bool = False

class HybridPDFParser:
    """Robust PDF parsing engine supporting PyMuPDF, pdfplumber, and OCR fallback for scanned documents."""

    def __init__(self, enable_ocr: bool = True):
        self.enable_ocr = enable_ocr

    def parse(self, filepath: Path) -> ParsedPDFDocument:
        """Parses PDF document with PyMuPDF, pdfplumber, table extraction, and OCR fallback."""
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return ParsedPDFDocument(
                filepath=str(filepath),
                filename=filepath.name,
                page_count=0,
                full_text="",
                is_corrupted=True
            )

        logger.info(f"Parsing PDF document: {filepath.name}")

        pages_text = []
        metadata = {}
        page_count = 0
        is_corrupted = False
        is_scanned = False

        # Step 1: Fast PyMuPDF (fitz) Extraction
        if fitz is not None:
            try:
                doc = fitz.open(str(filepath))
                page_count = len(doc)
                metadata = doc.metadata or {}

                for page_num in range(page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text("text") or ""
                    cleaned = self._clean_page_text(text)
                    pages_text.append(cleaned)
                doc.close()
            except Exception as e:
                logger.warning(f"PyMuPDF failed to parse {filepath.name}: {str(e)}")
                is_corrupted = True

        # Step 2: Fallback to pdfplumber text extraction if PyMuPDF failed or returned empty text
        if not pages_text or is_corrupted:
            try:
                pages_text = []
                with pdfplumber.open(str(filepath)) as pdf:
                    page_count = len(pdf.pages)
                    for page in pdf.pages:
                        text = page.extract_text() or ""
                        pages_text.append(self._clean_page_text(text))
                is_corrupted = False
            except Exception as e:
                logger.error(f"pdfplumber text extraction failed for {filepath.name}: {str(e)}")
                is_corrupted = True

        # Step 3: Check if document is scanned image PDF (text length < 50 chars per page)
        total_extracted_text = "\n\n".join(pages_text).strip()
        if page_count > 0 and len(total_extracted_text) < (30 * page_count):
            is_scanned = True
            logger.info(f"Document '{filepath.name}' detected as scanned image. Attempting OCR fallback...")
            
            if self.enable_ocr and HAS_OCR and fitz is not None:
                ocr_pages_text = self._perform_ocr_extraction(filepath)
                if ocr_pages_text:
                    pages_text = ocr_pages_text
                    total_extracted_text = "\n\n".join(pages_text)

        # Step 4: Table Extraction using pdfplumber
        tables = []
        if not is_corrupted:
            try:
                with pdfplumber.open(str(filepath)) as pdf:
                    for page in pdf.pages:
                        page_tables = page.extract_tables()
                        for tbl in page_tables:
                            cleaned_tbl = [
                                [self._clean_cell(cell) for cell in row]
                                for row in tbl if any(cell for cell in row)
                            ]
                            if cleaned_tbl:
                                tables.append(cleaned_tbl)
            except Exception as e:
                logger.warning(f"Table extraction warning for {filepath.name}: {str(e)}")

        return ParsedPDFDocument(
            filepath=str(filepath),
            filename=filepath.name,
            page_count=page_count,
            full_text=total_extracted_text,
            pages_text=pages_text,
            tables=tables,
            metadata=metadata,
            is_scanned=is_scanned,
            is_corrupted=is_corrupted
        )

    def _clean_page_text(self, text: str) -> str:
        """Cleans headers, footers, page numbering, and whitespace."""
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            stripped = line.strip()
            # Remove footers like "Page 1 of 4"
            if re.match(r"^Page\s+\d+(\s+of\s+\d+)?$", stripped, re.IGNORECASE):
                continue
            cleaned.append(line)
        result = "\n".join(cleaned)
        return re.sub(r"\n{3,}", "\n\n", result).strip()

    def _clean_cell(self, cell: Optional[str]) -> str:
        if cell is None:
            return ""
        return re.sub(r"\s+", " ", str(cell).replace("\n", " ").strip())

    def _perform_ocr_extraction(self, filepath: Path) -> List[str]:
        """Performs OCR extraction on scanned PDF pages using PyMuPDF pixmaps and pytesseract."""
        ocr_texts = []
        try:
            doc = fitz.open(str(filepath))
            for page in doc:
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img)
                ocr_texts.append(self._clean_page_text(text))
            doc.close()
        except Exception as e:
            logger.warning(f"OCR extraction failed for {filepath.name}: {str(e)}")
        return ocr_texts
