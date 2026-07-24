import re
from typing import Tuple, Dict, List
from src.logger import get_logger

logger = get_logger("Classifier")

class AnnouncementClassifier:
    """15-Taxonomy Classification Engine for Stock Market Corporate Announcements."""

    CATEGORIES = [
        "Order Win",
        "GST Notice",
        "Penalty",
        "Dividend",
        "Buyback",
        "Bonus",
        "Stock Split",
        "Acquisition",
        "Merger",
        "Partnership",
        "Expansion",
        "Litigation",
        "Management Change",
        "Credit Rating",
        "Other"
    ]

    PATTERNS: Dict[str, List[str]] = {
        "Order Win": [
            r"order\s+win", r"contract\s+awarded", r"purchase\s+order", r"letter\s+of\s+intent",
            r"loi", r"bhel\s+secured", r"won\s+order", r"award\s+of\s+contract", r"tender\s+win"
        ],
        "GST Notice": [
            r"gst\s+notice", r"section\s+73", r"section\s+74", r"goods\s+and\s+services\s+tax",
            r"show\s+cause\s+notice", r"demand\s+order\s+gst", r"input\s+tax\s+credit"
        ],
        "Penalty": [
            r"penalty", r"fine\s+imposed", r"sebi\s+penalty", r"regulatory\s+action",
            r"monetary\s+penalty", r"adjudication\s+order"
        ],
        "Dividend": [
            r"interim\s+dividend", r"final\s+dividend", r"special\s+dividend",
            r"recommendation\s+of\s+dividend", r"rs\.?\s*\d+\s+per\s+equity\s+share"
        ],
        "Buyback": [
            r"buyback", r"buy-back", r"repurchase\s+of\s+shares", r"tender\s+offer\s+buyback"
        ],
        "Bonus": [
            r"bonus\s+issue", r"bonus\s+shares", r"ratio\s+of\s+\d+:\d+", r"bonus\s+equity"
        ],
        "Stock Split": [
            r"stock\s+split", r"sub-division", r"split\s+of\s+shares", r"face\s+value\s+from"
        ],
        "Acquisition": [
            r"acquisition", r"acquired", r"takeover", r"purchase\s+of\s+stake",
            r"strategic\s+acquisition", r"slump\s+sale"
        ],
        "Merger": [
            r"merger", r"amalgamation", r"scheme\s+of\s+arrangement", r"demerger"
        ],
        "Partnership": [
            r"joint\s+venture", r"partnership", r"mou", r"memorandum\s+of\s+understanding",
            r"strategic\s+alliance", r"collaboration"
        ],
        "Expansion": [
            r"capacity\s+expansion", r"new\s+plant", r"greenfield", r"capital\s+expenditure",
            r"capex", r"commercial\s+production"
        ],
        "Litigation": [
            r"litigation", r"court\s+case", r"high\s+court", r"supreme\s+court",
            r"arbitration", r"legal\s+dispute", r"summons"
        ],
        "Management Change": [
            r"resignation", r"appointment", r"cfo", r"ceo", r"managing\s+director",
            r"key\s+managerial\s+personnel", r"kmp\s+change"
        ],
        "Credit Rating": [
            r"credit\s+rating", r"rating\s+downgrade", r"crisil", r"icra", r"care\s+edge",
            r"rating\s+reaffirmed", r"rating\s+revised"
        ]
    }

    def classify(self, text: str, filename: str = "") -> Tuple[str, float]:
        """Classifies text into one of 15 standard corporate action categories with confidence score."""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        scores: Dict[str, float] = {cat: 0.0 for cat in self.CATEGORIES}

        # Check keyword pattern matches
        for cat, patterns in self.PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    scores[cat] += 1.0
                if re.search(pat, filename_lower):
                    scores[cat] += 2.0  # Filename indicator has higher weight

        top_category = max(scores, key=scores.get)
        top_score = scores[top_category]

        if top_score == 0.0:
            return "Other", 0.50

        # Calculate normalized confidence score
        confidence = min(0.98, max(0.65, 0.60 + (top_score * 0.10)))
        return top_category, round(confidence, 2)
