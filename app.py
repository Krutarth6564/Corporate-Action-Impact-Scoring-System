import os
import streamlit as st
import pandas as pd
from pathlib import Path

from config.config import RAW_DATA_DIR, OUTPUT_DIR
from src.downloader import ResilientPDFDownloader
from src.pdf_parser import HybridPDFParser
from src.ranker import ImpactRankingPipeline
from src.dashboard import inject_theme, render_header, render_kpis, render_company_score_cards, render_charts, render_detail_inspector
from src.logger import get_logger

# Streamlit Page Configuration
st.set_page_config(
    page_title="Corporate Action Impact Scoring System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = get_logger("App")

def main():
    inject_theme()
    render_header()

    # Sidebar Control Center
    st.sidebar.title("Control Center")
    st.sidebar.markdown("---")

    # AI Config
    st.sidebar.subheader("AI Scoring Configuration")
    use_llm = st.sidebar.checkbox("Enable OpenAI LLM Enhancement", value=False)
    if use_llm:
        api_key_input = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        if api_key_input:
            os.environ["OPENAI_API_KEY"] = api_key_input

    st.sidebar.markdown("---")
    st.sidebar.subheader("PDF Document Management")

    # PDF Uploader
    uploaded_files = st.sidebar.file_uploader(
        "Upload Corporate Action PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_uploader_widget"
    )
    
    if uploaded_files:
        uploaded_names = [f.name for f in uploaded_files]
        last_uploaded = st.session_state.get("last_uploaded_names", [])

        if uploaded_names != last_uploaded:
            for u_file in uploaded_files:
                save_path = RAW_DATA_DIR / u_file.name
                with open(save_path, "wb") as f:
                    f.write(u_file.getbuffer())
            st.session_state["last_uploaded_names"] = uploaded_names
            # Clear cache so pipeline re-runs immediately with newly uploaded files
            st.session_state.pop("pipeline_data", None)
            st.sidebar.success(f"Saved {len(uploaded_files)} file(s). Generating scores...")

    # Action buttons
    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("Score PDFs", type="primary", width='stretch'):
            st.session_state.pop("pipeline_data", None)
            st.rerun()

    with col_btn2:
        if st.button("Reset Samples", width='stretch'):
            with st.spinner("Generating sample corporate PDFs..."):
                _create_samples(RAW_DATA_DIR)
                st.sidebar.success("Reset 5 sample PDFs!")
                st.session_state.pop("pipeline_data", None)
                st.rerun()

    st.sidebar.markdown("---")

    # Available PDFs (Automatically download missing assignment PDFs on startup)
    pdf_paths = list(RAW_DATA_DIR.glob("*.pdf"))
    if len(pdf_paths) < 5:
        with st.spinner("Ensuring all 5 assignment corporate PDFs are downloaded..."):
            downloader = ResilientPDFDownloader(dest_dir=RAW_DATA_DIR)
            downloader.download_assignment_pdfs()
            pdf_paths = list(RAW_DATA_DIR.glob("*.pdf"))

    # Pipeline Trigger Button
    if "pipeline_data" not in st.session_state or st.sidebar.button("Run Impact Scoring Pipeline", type="primary", width='stretch'):
        progress_bar = st.progress(0)
        status_text = st.empty()

        pipeline = ImpactRankingPipeline(use_llm=use_llm)
        records = []

        total_files = len(pdf_paths)
        for idx, pdf_path in enumerate(pdf_paths, start=1):
            status_text.text(f"Processing ({idx}/{total_files}): {pdf_path.name}")
            progress_bar.progress(int((idx / total_files) * 100))

        records, df = pipeline.process_pdf_paths(pdf_paths)
        st.session_state["pipeline_data"] = (records, df)
        status_text.empty()
        progress_bar.empty()

    records, df = st.session_state.get("pipeline_data", ([], pd.DataFrame()))

    if df.empty:
        st.warning("No PDF filings analyzed. Click 'Run Impact Scoring Pipeline' to begin.")
        return

    # Sidebar Filter Controls
    st.sidebar.subheader("Filters & Search")
    company_search = st.sidebar.text_input("Search Company / Ticker").upper().strip()

    all_sectors = sorted(list(df["sector"].unique()))
    selected_sectors = st.sidebar.multiselect("Sector Filter", all_sectors, default=all_sectors)

    all_types = sorted(list(df["announcement_type"].unique()))
    selected_types = st.sidebar.multiselect("Announcement Type Filter", all_types, default=all_types)

    min_score = st.sidebar.slider("Minimum Impact Score", 0.0, 100.0, 0.0, step=5.0)

    # Apply Filters
    filtered_df = df[
        (df["impact_score"] >= min_score) &
        (df["sector"].isin(selected_sectors)) &
        (df["announcement_type"].isin(selected_types))
    ]
    if company_search:
        filtered_df = filtered_df[
            filtered_df["ticker"].str.contains(company_search, na=False) |
            filtered_df["company_name"].str.contains(company_search, case=False, na=False)
        ]

    filtered_records = [r for r in records if r.filename in filtered_df["filename"].values]

    # Compute KPI Stats
    pipeline = ImpactRankingPipeline()
    summary = pipeline.compute_summary_statistics(filtered_records)

    # Render Dashboard Components
    render_kpis(summary)
    st.markdown("---")

    render_company_score_cards(filtered_df)
    st.markdown("---")

    # Select Box for Deep-Dive Inspector and Gauge Chart
    selected_file = None
    selected_row = None
    if not filtered_df.empty:
        selected_file = st.selectbox("Select Corporate Filing to Inspect & View Gauge Score:", filtered_df["filename"].tolist())
        selected_row = filtered_df[filtered_df["filename"] == selected_file].iloc[0]

    render_charts(filtered_df, selected_row=selected_row)
    st.markdown("---")

    # Multi-Format Download Section
    st.subheader("Leaderboard & Export Center")
    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)

    with dl_col1:
        csv_path = OUTPUT_DIR / "corporate_action_impact_report.csv"
        if csv_path.exists():
            with open(csv_path, "rb") as f:
                st.download_button("📥 Download CSV", data=f, file_name="impact_scores.csv", mime="text/csv", width='stretch')

    with dl_col2:
        excel_path = OUTPUT_DIR / "corporate_action_impact_report.xlsx"
        if excel_path.exists():
            with open(excel_path, "rb") as f:
                st.download_button("📥 Download Excel", data=f, file_name="impact_scores.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width='stretch')

    with dl_col3:
        json_path = OUTPUT_DIR / "corporate_action_impact_report.json"
        if json_path.exists():
            with open(json_path, "rb") as f:
                st.download_button("📥 Download JSON", data=f, file_name="impact_scores.json", mime="application/json", width='stretch')

    with dl_col4:
        pdf_rep_path = OUTPUT_DIR / "corporate_action_impact_report.pdf"
        if pdf_rep_path.exists():
            with open(pdf_rep_path, "rb") as f:
                st.download_button("📥 Download PDF Report", data=f, file_name="impact_report.pdf", mime="application/pdf", width='stretch')

    # Ranked Table
    display_cols = ["rank", "ticker", "company_name", "announcement_type", "sector", "impact_score", "impact_rating", "formatted_contract_value"]
    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "rank": st.column_config.NumberColumn("Rank", format="#%d"),
            "ticker": st.column_config.TextColumn("Ticker"),
            "company_name": st.column_config.TextColumn("Company Name"),
            "announcement_type": st.column_config.TextColumn("Category"),
            "sector": st.column_config.TextColumn("Sector"),
            "impact_score": st.column_config.NumberColumn("Impact Score", format="%.1f / 100"),
            "impact_rating": st.column_config.TextColumn("Rating Tag"),
            "formatted_contract_value": st.column_config.TextColumn("Disclosed Value")
        },
        hide_index=True,
        width='stretch'
    )

    st.markdown("---")

    # Announcement Inspector
    st.subheader("Deep-Dive Filing Inspector")
    if selected_row is not None:
        render_detail_inspector(selected_row)

def _create_samples(dest_dir: Path):
    """Creates initial synthetic sample corporate PDFs in dest_dir."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    samples = [
        {"filename": "BHEL_Govt_Order_Win.pdf", "ticker": "BHEL", "company": "Bharat Heavy Electricals Limited", "category": "Order Win", "title": "AWARD OF MAJOR GOVERNMENT CONTRACT", "content": "BHEL has secured a prestigious government order worth INR 620 Crores from NTPC for capacity expansion of thermal power station."},
        {"filename": "TCS_Dividend_Declaration.pdf", "ticker": "TCS", "company": "Tata Consultancy Services Limited", "category": "Dividend", "title": "DECLARATION OF INTERIM DIVIDEND", "content": "The Board of Directors declared an Interim Dividend of Rs 28 per equity share with Record Date July 30, 2026. Total cash payout stands at INR 10,200 Crores."},
        {"filename": "SUZLON_Debt_Default.pdf", "ticker": "SUZLON", "company": "Suzlon Energy Limited", "category": "Debt Default & Downgrade", "title": "DISCLOSURE OF DEBT INTEREST DEFAULT", "content": "The Company defaulted on an interest payment of INR 145.5 Crores due on NCDs. CRISIL has downgraded rating to D (Default)."},
        {"filename": "RELIANCE_Strategic_M&A.pdf", "ticker": "RELIANCE", "company": "Reliance Industries Limited", "category": "Merger & Acquisition", "title": "STRATEGIC GREEN HYDROGEN ACQUISITION", "content": "Approved 100% equity stake acquisition in GreenTech Energy Solutions for INR 4,500 Crores."},
        {"filename": "INFY_GST_Demand_Notice.pdf", "ticker": "INFY", "company": "Infosys Limited", "category": "GST Notice", "title": "RECEIPT OF GST DEMAND NOTICE UNDER SECTION 73", "content": "Received a show cause GST notice demanding tax liability of INR 32.4 Crores along with applicable interest and penalty."}
    ]

    styles = getSampleStyleSheet()
    for s in samples:
        fpath = dest_dir / s["filename"]
        doc = SimpleDocTemplate(str(fpath), pagesize=letter)
        elems = [
            Paragraph(f"<b>{s['company']} ({s['ticker']})</b>", styles['Heading1']),
            HRFlowable(width="100%", color=colors.HexColor('#0F766E')),
            Spacer(1, 10),
            Paragraph(f"<b>{s['title']}</b>", styles['Heading2']),
            Spacer(1, 8),
            Paragraph(s["content"], styles['Normal'])
        ]
        doc.build(elems)

if __name__ == "__main__":
    main()
