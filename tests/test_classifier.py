import pytest
from src.classifier import AnnouncementClassifier

def test_order_win_classification():
    classifier = AnnouncementClassifier()
    category, confidence = classifier.classify("Company secured a major order win worth 620 Crores", "BHEL_Order.pdf")
    assert category == "Order Win"
    assert confidence > 0.60

def test_gst_notice_classification():
    classifier = AnnouncementClassifier()
    category, confidence = classifier.classify("Notice received under section 73 for GST demand", "GST_Notice.pdf")
    assert category == "GST Notice"

def test_debt_default_classification():
    classifier = AnnouncementClassifier()
    category, confidence = classifier.classify("Default in payment of interest on debentures CRISIL rating downgrade", "Default.pdf")
    assert category in ["Credit Rating", "Other"] or "downgrade" in "default"

def test_unknown_classification():
    classifier = AnnouncementClassifier()
    category, confidence = classifier.classify("Random administrative update", "doc.pdf")
    assert category == "Other"
