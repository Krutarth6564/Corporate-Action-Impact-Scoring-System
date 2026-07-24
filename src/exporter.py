import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from config.config import OUTPUT_DIR
from src.validator import CorporateActionRecord
from src.logger import get_logger

logger = get_logger("Exporter")

class MultiFormatExporter:
    """Exports ranked corporate action analytics to CSV, Excel, JSON, and PDF analytical reports."""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir

    def export_all(self, records: List[CorporateActionRecord], base_filename: str = "corporate_action_impact_report") -> Dict[str, Path]:
        """Exports records into CSV, Excel, JSON, and PDF report files."""
        exported_paths = {}

        dicts = [r.model_dump() for r in records]
        df = pd.DataFrame(dicts)

        # 1. Export CSV
        csv_path = self.output_dir / f"{base_filename}.csv"
        try:
            df.to_csv(csv_path, index=False)
            exported_paths["csv"] = csv_path
            logger.info(f"Exported CSV report: {csv_path.name}")
        except Exception as e:
            logger.error(f"Failed CSV export: {str(e)}")

        # 2. Export Excel
        excel_path = self.output_dir / f"{base_filename}.xlsx"
        try:
            df.to_excel(excel_path, index=False, engine="openpyxl")
            exported_paths["excel"] = excel_path
            logger.info(f"Exported Excel report: {excel_path.name}")
        except Exception as e:
            logger.error(f"Failed Excel export: {str(e)}")

        # 3. Export JSON
        json_path = self.output_dir / f"{base_filename}.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(dicts, f, indent=4, ensure_ascii=False)
            exported_paths["json"] = json_path
            logger.info(f"Exported JSON report: {json_path.name}")
        except Exception as e:
            logger.error(f"Failed JSON export: {str(e)}")

        # 4. Export PDF Analytical Report
        pdf_path = self.output_dir / f"{base_filename}.pdf"
        try:
            self._export_pdf_report(records, pdf_path)
            exported_paths["pdf"] = pdf_path
            logger.info(f"Exported PDF executive report: {pdf_path.name}")
        except Exception as e:
            logger.error(f"Failed PDF report export: {str(e)}")

        # 5. Export Alias Files (impact_scores_ranked.csv / json)
        try:
            df.to_csv(self.output_dir / "impact_scores_ranked.csv", index=False)
            with open(self.output_dir / "impact_scores_ranked.json", "w", encoding="utf-8") as f:
                json.dump(dicts, f, indent=4, ensure_ascii=False)
            logger.info("Exported impact_scores_ranked.csv and impact_scores_ranked.json")
        except Exception as e:
            logger.error(f"Failed impact_scores_ranked export: {str(e)}")

        return exported_paths

    def _export_pdf_report(self, records: List[CorporateActionRecord], filepath: Path) -> None:
        """Generates a formatted PDF executive market report using ReportLab."""
        doc = SimpleDocTemplate(str(filepath), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'))
        body_style = ParagraphStyle('ReportBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#334155'))

        elements = [
            Paragraph("<b>Corporate Action Impact Scoring Report</b>", title_style),
            Paragraph("Automated Market Materiality Analytics & Ranking Executive Summary", body_style),
            HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F766E'), spaceAfter=12),
            Spacer(1, 10)
        ]

        table_data = [["Rank", "Ticker", "Company Name", "Category", "Score", "Rating", "Disclosed Value"]]
        for r in records:
            table_data.append([
                str(r.rank or "-"),
                r.ticker,
                r.company_name[:24],
                r.announcement_type,
                f"{r.impact_score:.1f}",
                r.impact_rating,
                r.formatted_contract_value
            ])

        t = Table(table_data, colWidths=[35, 60, 140, 110, 45, 65, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#FFFFFF')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        doc.build(elements)
