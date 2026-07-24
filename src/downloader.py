import os
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.config import RAW_DATA_DIR, REQUEST_TIMEOUT, MAX_RETRIES, DEFAULT_USER_AGENT
from src.logger import get_logger

logger = get_logger("Downloader")

def calculate_file_hash(filepath: Path) -> str:
    """Computes SHA-256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_retry_session(retries: int = MAX_RETRIES, backoff_factor: float = 0.5) -> requests.Session:
    """Creates a requests HTTP Session configured with exponential backoff retries and browser headers."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    })
    return session

class ResilientPDFDownloader:
    """Production PDF Downloader supporting multi-URL batching, retries, duplicate detection, and progress callbacks."""

    def __init__(self, dest_dir: Path = RAW_DATA_DIR):
        self.dest_dir = dest_dir
        self.session = get_retry_session()
        self.existing_hashes = self._index_existing_hashes()

    def _index_existing_hashes(self) -> Dict[str, Path]:
        """Indexes SHA-256 hashes of all existing PDFs in raw data directory."""
        hashes = {}
        for pdf_file in self.dest_dir.glob("*.pdf"):
            try:
                h = calculate_file_hash(pdf_file)
                hashes[h] = pdf_file
            except Exception as e:
                logger.warning(f"Could not hash existing file {pdf_file.name}: {str(e)}")
        return hashes

    def download_url(self, url: str, custom_filename: Optional[str] = None) -> Optional[Path]:
        """Downloads a single PDF URL with retries, timeout, and hash duplicate detection."""
        if not self._is_valid_url(url):
            logger.error(f"Invalid URL provided: '{url}'")
            return None

        filename = custom_filename or os.path.basename(urlparse(url).path)
        if not filename or not filename.endswith(".pdf"):
            filename = f"announcement_{hashlib.md5(url.encode()).hexdigest()[:8]}.pdf"

        dest_path = self.dest_dir / filename

        try:
            logger.info(f"Initiating download: {url}")
            domain = urlparse(url).netloc
            request_headers = {"User-Agent": DEFAULT_USER_AGENT}
            if "bseindia" in domain:
                request_headers["Referer"] = "https://www.bseindia.com/"
                request_headers["Accept"] = "application/pdf,*/*"
            elif "nseindia" in domain:
                request_headers["Referer"] = "https://www.nseindia.com/"
                request_headers["Accept"] = "application/pdf,*/*"

            response = self.session.get(url, headers=request_headers, timeout=REQUEST_TIMEOUT, stream=True)
            response.raise_for_status()

            temp_path = self.dest_dir / f"temp_{filename}"
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Validate non-empty file & PDF magic bytes (%PDF-)
            if temp_path.stat().st_size == 0:
                logger.error(f"Downloaded PDF from {url} is empty (0 bytes).")
                temp_path.unlink(missing_ok=True)
                return None

            with open(temp_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    logger.warning(f"Response from {url} did not begin with %PDF- header. Preserving file.")

            # SHA-256 Duplicate Check
            file_hash = calculate_file_hash(temp_path)
            if file_hash in self.existing_hashes:
                logger.info(f"Duplicate PDF detected (hash match with {self.existing_hashes[file_hash].name}). Skipping.")
                temp_path.unlink(missing_ok=True)
                return self.existing_hashes[file_hash]

            # Save valid new file
            temp_path.rename(dest_path)
            self.existing_hashes[file_hash] = dest_path
            logger.info(f"Successfully downloaded new PDF: {dest_path.name}")
            return dest_path

        except Exception as e:
            if dest_path.exists() and dest_path.stat().st_size > 0:
                logger.warning(f"Download HTTP error for {url} ({str(e)}). Reusing cached local file: {dest_path.name}")
                return dest_path
            logger.error(f"Failed to download PDF from {url}: {str(e)}")
            return None

    def download_assignment_pdfs(self) -> List[Path]:
        """Ensures all 5 assignment source PDFs are present in data/raw/."""
        from config.assignment_urls import ASSIGNMENT_PDF_URLS
        return self.download_batch(ASSIGNMENT_PDF_URLS)

    def download_batch(
        self,
        urls: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Path]:
        """Downloads a batch of PDF URLs with progress tracking."""
        downloaded = []
        total = len(urls)

        for idx, url in enumerate(urls, start=1):
            if progress_callback:
                progress_callback(idx, total, f"Downloading {idx}/{total}: {url}")

            path = self.download_url(url)
            if path:
                downloaded.append(path)

        return downloaded

    def _is_valid_url(self, url: str) -> bool:
        """Validates HTTP/HTTPS URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme in ["http", "https"], result.netloc])
        except Exception:
            return False
