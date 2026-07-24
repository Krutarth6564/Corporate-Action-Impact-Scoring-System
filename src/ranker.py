import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

from config.config import RAW_DATA_DIR, OUTPUT_DIR
from src.pdf_parser import HybridPDFParser, ParsedPDFDocument
from src.extractor import AdvancedInformationExtractor
from src.scorer import ExplainableImpactScorer
from src.summarizer import BusinessSummarizer
from src.exporter import MultiFormatExporter
from src.validator import CorporateActionRecord
from src.logger import get_logger

logger = get_logger("Ranker")

class ImpactRankingPipeline:
    """End-to-end processing pipeline to parse, extract, score, summarize, rank, and export corporate actions."""

    def __init__(self, use_llm: bool = False):
        self.parser = HybridPDFParser()
        self.extractor = AdvancedInformationExtractor(use_llm=use_llm)
        self.scorer = ExplainableImpactScorer()
        self.summarizer = BusinessSummarizer(use_llm=use_llm)
        self.exporter = MultiFormatExporter()

    def process_pdf_paths(self, pdf_paths: List[Path]) -> Tuple[List[CorporateActionRecord], pd.DataFrame]:
        """Processes a list of PDF paths, produces ranked records, and exports all report formats."""
        records: List[CorporateActionRecord] = []
        logger.info(f"Starting batch execution for {len(pdf_paths)} announcements...")

        for pdf_path in pdf_paths:
            try:
                # 1. Parse PDF
                pdf_doc = self.parser.parse(pdf_path)
                
                # 2. Extract Entities
                record = self.extractor.extract(pdf_doc)
                
                # 3. Score Impact
                record = self.scorer.score(record)
                
                # 4. Generate AI Business Summary
                record.summary = self.summarizer.generate_summary(record, pdf_doc.full_text)

                records.append(record)
                logger.info(f"Processed '{pdf_doc.filename}': Score {record.impact_score}/100 ({record.impact_rating})")
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {str(e)}")

        if not records:
            return [], pd.DataFrame()

        # Sort descending by Impact Score
        records.sort(key=lambda r: r.impact_score, reverse=True)

        # Assign Ranks
        for idx, rec in enumerate(records, start=1):
            rec.rank = idx

        # Export Multi-format files
        self.exporter.export_all(records)

        # Convert to pandas DataFrame
        df = pd.DataFrame([r.model_dump() for r in records])
        return records, df

    def compute_summary_statistics(self, records: List[CorporateActionRecord]) -> Dict[str, Any]:
        """Calculates executive dashboard stats."""
        if not records:
            return {
                "total_processed": 0,
                "very_high_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "avg_impact_score": 0.0,
                "top_announcement": "N/A"
            }

        return {
            "total_processed": len(records),
            "very_high_count": sum(1 for r in records if r.impact_rating == "Very High"),
            "high_count": sum(1 for r in records if r.impact_rating == "High"),
            "medium_count": sum(1 for r in records if r.impact_rating == "Medium"),
            "low_count": sum(1 for r in records if r.impact_rating == "Low"),
            "avg_impact_score": round(sum(r.impact_score for r in records) / len(records), 1),
            "top_announcement": f"{records[0].ticker} - {records[0].announcement_type} ({records[0].impact_score})"
        }
