import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
MODELS_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "assets"

def setup_logger(name: str = "CorporateActionImpact", log_level: str = None) -> logging.Logger:
    """Configures and returns a structured logger."""
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    numeric_level = getattr(logging, log_level, logging.INFO)
    
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Optional file logger in output directory
        ensure_directories()
        file_handler = logging.FileHandler(OUTPUT_DIR / "system.log", encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def ensure_directories() -> None:
    """Ensures all required project directories exist."""
    for directory in [DATA_DIR, OUTPUT_DIR, MODELS_DIR, ASSETS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def save_json(data: Any, filepath: Path) -> bool:
    """Saves dictionary or list data to a JSON file safely."""
    try:
        ensure_directories()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger = setup_logger()
        logger.error(f"Failed to save JSON to {filepath}: {str(e)}")
        return False

def load_json(filepath: Path) -> Optional[Any]:
    """Loads data from a JSON file safely."""
    try:
        if not filepath.exists():
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger = setup_logger()
        logger.error(f"Failed to load JSON from {filepath}: {str(e)}")
        return None

def save_dataframe_csv(df: pd.DataFrame, filepath: Path) -> bool:
    """Saves DataFrame to CSV safely."""
    try:
        ensure_directories()
        df.to_csv(filepath, index=False)
        return True
    except Exception as e:
        logger = setup_logger()
        logger.error(f"Failed to save DataFrame CSV to {filepath}: {str(e)}")
        return False

def format_currency_inr(amount: float) -> str:
    """Formats numeric values into INR representation (Crores/Lakhs/K)."""
    if amount is None or pd.isna(amount):
        return "N/A"
    
    if amount >= 10_000_000: # 1 Crore = 10,000,000
        return f"₹{amount / 10_000_000:.2f} Cr"
    elif amount >= 100_000: # 1 Lakh = 100,000
        return f"₹{amount / 100_000:.2f} Lakh"
    elif amount >= 1000:
        return f"₹{amount / 1000:.2f} K"
    else:
        return f"₹{amount:.2f}"
