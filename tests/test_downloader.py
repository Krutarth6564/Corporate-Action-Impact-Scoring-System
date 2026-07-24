import pytest
from src.downloader import ResilientPDFDownloader

def test_url_validation():
    downloader = ResilientPDFDownloader()
    assert downloader._is_valid_url("https://www.bseindia.com/pdf/announcement.pdf") is True
    assert downloader._is_valid_url("not_a_valid_url") is False
