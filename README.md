# Corporate Action Impact Scoring System 📈

An enterprise-grade, production-ready AI platform designed to analyze NSE/BSE corporate announcement PDFs, extract 25+ detailed financial metrics, classify disclosures into 15 standard corporate action categories, and calculate an **explainable market impact score (0 - 100)** estimating stock price materiality.

---

## 🌟 Key System Capabilities

- **Taxonomy Announcement Classifier**: Categorizes announcements into `Order Win`, `GST Notice`, `Penalty`, `Dividend`, `Buyback`, `Bonus`, `Stock Split`, `Merger`, `Credit Rating`, and `Other`.
- **Explainable Weighted Scoring Engine**: Multi-factor scoring (0 to 100) powered by configurable `config/scoring.yaml` weights, assigning 4 rating tags (`Very High`, `High`, `Medium`, `Low`) and natural language explanations.
- **AI Executive Business Summarizer**: Produces 1-2 sentence market summaries (e.g. *"BHEL secured a ₹620 crore government order expected to positively impact future revenues. Overall market impact is High."*).
- **Multi-Format Export Engine**: Exports ranked corporate intelligence into CSV, Excel (`openpyxl`), JSON, and formatted PDF executive reports (`reportlab`).
- **Streamlit & Plotly Interactive Dashboard**:
  - Dark-mode responsive layout.
  - Sidebar multi-filters (Company search, Sector multiselect, Announcement type multiselect, Minimum impact score slider).
  - Plotly Gauge Chart for top filing score.
  - Pie Chart for category breakdown.
  - Score distribution histogram and horizontal bar charts.
  - Multi-format download buttons (CSV, Excel, JSON, PDF report).
  - Expandable company deep-dive inspector with score factor decomposition.
- **Automated Pytest Test Suite**: Unit test suite covering downloader, parser, extractor, classifier, scorer, ranker, and dashboard components.

---

## 📁 Project Architecture & Assignment Mapping

```
Corporate_Action_Impact/
│
├── config/
│   ├── config.py             # System path & environment configuration
│   └── scoring.yaml          # Configurable scoring weight parameters
│
├── data/
│   ├── raw/                  # Raw input PDFs
│   └── processed/            # Extracted & structured JSON cache
│
├── output/                   # Generated reports (CSV, Excel, JSON, PDF)
├── logs/                     # Centralized app log files
├── assets/                   # Visual assets & icons
├── models/                   # spaCy models / cache
├── tests/                    # Pytest test suite
│   ├── test_classifier.py
│   ├── test_downloader.py
│   ├── test_extractor.py
│   ├── test_parser.py
│   └── test_scorer.py
│
├── src/
│   ├── logger.py             # Centralized structured logging setup
│   ├── validator.py          # Pydantic data schemas
│   ├── downloader.py         # Resilient multi-URL PDF downloader
│   ├── pdf_parser.py         # PyMuPDF + pdfplumber + OCR engine
│   ├── extractor.py          # spaCy + Regex entity extraction engine
│   ├── classifier.py         # 15-category corporate action classifier
│   ├── scorer.py             # Configurable explainable impact scoring
│   ├── ranker.py             # Sorting, ranking & leaderboard engine
│   ├── summarizer.py         # Rule-based & LLM executive summarizer
│   ├── exporter.py           # Multi-format exporter (CSV, Excel, JSON, PDF)
│   ├── dashboard.py          # Streamlit UI visual components & Gauge charts
│   └── utils.py              # File helpers, hash calculation, text cleaning
│
├── app.py                    # Main Streamlit web application
├── requirements.txt          # Production dependencies
├── README.md                 # System documentation
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusion rules
└── LICENSE                   # MIT License
```

---

## ⚙️ Installation & Usage Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Pytest Suite
```bash
pytest tests/ -v
```

### 3. Launch Streamlit Interactive Dashboard
```bash
streamlit run app.py
```

---

## 📊 Impact Rating Taxonomy

| Score Range | Rating Tag | Description |
| :--- | :--- | :--- |
| **85.0 - 100.0** | `Very High` | Massive market materiality (Debt defaults, CFO resignations, large M&A). |
| **70.0 - 84.9** | `High` | Significant financial impact (Quarterly earnings, large dividends, capex plans). |
| **45.0 - 69.9** | `Medium` | Moderate significance (Mid-sized order wins, bonus shares, routine board outcomes). |
| **0.0 - 44.9** | `Low` | Minor routine filings (General disclosures, meeting notices). |

---

## 🛡️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
