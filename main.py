import sys
from pathlib import Path
import pandas as pd

from config.config import BASE_DIR, RAW_DATA_DIR, OUTPUT_DIR
from config.assignment_urls import ASSIGNMENT_PDF_URLS
from src.downloader import ResilientPDFDownloader
from src.ranker import ImpactRankingPipeline
from src.logger import get_logger

logger = get_logger("Main")

SYNTHETIC_FILES_TO_REMOVE = [
    # Synthetic files in data/raw/
    RAW_DATA_DIR / "BHEL_Govt_Order_Win.pdf",
    RAW_DATA_DIR / "INFY_GST_Demand_Notice.pdf",
    RAW_DATA_DIR / "RELIANCE_Strategic_M&A.pdf",
    RAW_DATA_DIR / "SUZLON_Debt_Default.pdf",
    RAW_DATA_DIR / "TCS_Dividend_Declaration.pdf",
    # Unrelated sample files directly in data/
    BASE_DIR / "data" / "INFY_Board_Resignation_CEO_Notice.pdf",
    BASE_DIR / "data" / "RELIANCE_Merger_Acquisition_Notice.pdf",
    BASE_DIR / "data" / "SUZLON_Debt_Default_Disclosure.pdf",
    BASE_DIR / "data" / "TATAMOTORS_Bonus_Issue_Ratio.pdf",
    BASE_DIR / "data" / "TCS_Q1_Financial_Results_Dividend.pdf"
]

def clean_placeholder_files():
    """Removes placeholder synthetic PDFs to maintain clean source dataset."""
    for fpath in SYNTHETIC_FILES_TO_REMOVE:
        if fpath.exists():
            try:
                fpath.unlink()
                logger.info(f"Removed placeholder file: {fpath.name}")
            except Exception as e:
                logger.warning(f"Could not remove {fpath.name}: {str(e)}")

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 80)
    print("  CORPORATE ACTION IMPACT SCORING SYSTEM - NON-INTERACTIVE ENTRYPOINT")
    print("=" * 80)

    # 1. Clean Stale Placeholder PDFs
    clean_placeholder_files()

    # 2. Download 5 Source PDFs
    downloader = ResilientPDFDownloader(dest_dir=RAW_DATA_DIR)
    print("\n[Step 1/3] Downloading 5 Source Corporate Announcement PDFs...")
    downloaded_paths = downloader.download_batch(ASSIGNMENT_PDF_URLS)
    
    if not downloaded_paths:
        # Fallback to any existing PDFs in RAW_DATA_DIR if network download fails
        downloaded_paths = list(RAW_DATA_DIR.glob("*.pdf"))

    print(f"-> Total valid PDFs for processing: {len(downloaded_paths)}")

    # 3. Process & Rank PDFs
    print("\n[Step 2/3] Processing, Classifying, Scoring & Ranking Filings...")
    pipeline = ImpactRankingPipeline(use_llm=False)
    records, df = pipeline.process_pdf_paths(downloaded_paths)

    # 4. Output Summary Table
    print("\n[Step 3/3] Generated Ranked Corporate Action Impact Summary:\n")
    if not df.empty:
        summary_df = df[["rank", "ticker", "company_name", "announcement_type", "impact_score", "impact_rating", "formatted_contract_value"]]
        print(summary_df.to_string(index=False))
        print(f"\n[OK] Reports saved to {OUTPUT_DIR.resolve()}:")
        print("  - corporate_action_impact_report.csv")
        print("  - corporate_action_impact_report.xlsx")
        print("  - corporate_action_impact_report.json")
        print("  - corporate_action_impact_report.pdf")
        print("  - impact_scores_ranked.csv")
        print("  - impact_scores_ranked.json")
    else:
        print("[!] No records were processed.")

    print("\n=" * 80)
    print("  PIPELINE EXECUTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
