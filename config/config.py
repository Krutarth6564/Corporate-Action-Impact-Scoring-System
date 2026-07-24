import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Directory Paths
CONFIG_DIR = BASE_DIR / "config"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
MODELS_DIR = BASE_DIR / "models"
TESTS_DIR = BASE_DIR / "tests"

# Create directories if they do not exist
for path in [CONFIG_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR, LOGS_DIR, ASSETS_DIR, MODELS_DIR, TESTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# System Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
DEFAULT_USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

def load_scoring_config() -> Dict[str, Any]:
    """Loads scoring weights from YAML or returns default structure."""
    yaml_path = CONFIG_DIR / "scoring.yaml"
    if yaml_path.exists():
        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass

    # Fallback weights
    return {
        "category_weights": {
            "Debt Default & Downgrade": 45.0,
            "Litigation & Court Case": 40.0,
            "Penalty & Tax Demand": 38.0,
            "GST Notice": 35.0,
            "Merger & Acquisition": 35.0,
            "Financial Results": 30.0,
            "Order Win": 28.0,
            "Buyback & Dividend": 25.0,
            "Bonus & Stock Split": 25.0,
            "Management Change": 24.0,
            "Credit Rating": 22.0,
            "Expansion & Capex": 20.0,
            "Partnership": 18.0,
            "Other Disclosure": 10.0
        },
        "financial_scale_thresholds": {
            "very_large_cr": 5000.0,
            "large_cr": 1000.0,
            "medium_cr": 250.0,
            "small_cr": 50.0,
            "minor_cr": 10.0
        },
        "rating_thresholds": {
            "very_high": 85.0,
            "high": 70.0,
            "medium": 45.0,
            "low": 0.0
        }
    }
