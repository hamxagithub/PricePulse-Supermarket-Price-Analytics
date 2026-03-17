"""
Abstract base scraper with retry logic, exponential backoff,
rate limiting, structured logging, and pagination handling.
"""
import abc
import csv
import logging
import os
import time
from datetime import datetime

import requests

import config


class BaseScraper(abc.ABC):
    """Base class for all store scrapers."""

    def __init__(self, store_key: str):
        self.store_key = store_key
        self.store_cfg = config.STORES[store_key]
        self.store_name = self.store_cfg["name"]
        self.cities = self.store_cfg["cities"]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self._setup_logger()

    # ── Logging ────────────────────────────────────────────────
    def _setup_logger(self):
        self.logger = logging.getLogger(f"scraper.{self.store_key}")
        self.logger.setLevel(logging.DEBUG)
        # File handler
        log_file = os.path.join(
            config.LOGS_DIR,
            f"{self.store_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        )
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        fh.setFormatter(fmt)
        ch.setFormatter(fmt)
        if not self.logger.handlers:
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    # ── Retry with Exponential Backoff ─────────────────────────
    def request_with_retry(self, url, params=None, method="GET"):
        """Make an HTTP request with retry logic and rate limiting."""
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                self.logger.debug(
                    f"Request attempt {attempt}/{config.MAX_RETRIES}: {url}"
                )
                if method == "GET":
                    resp = self.session.get(
                        url, params=params, timeout=config.REQUEST_TIMEOUT
                    )
                else:
                    resp = self.session.post(
                        url, data=params, timeout=config.REQUEST_TIMEOUT
                    )
                resp.raise_for_status()
                # Rate limiting
                time.sleep(config.RATE_LIMIT_DELAY)
                return resp
            except requests.exceptions.RequestException as e:
                wait = config.RETRY_BACKOFF_FACTOR ** attempt
                self.logger.warning(
                    f"Request failed (attempt {attempt}): {e}. "
                    f"Retrying in {wait:.1f}s..."
                )
                if attempt < config.MAX_RETRIES:
                    time.sleep(wait)
                else:
                    self.logger.error(
                        f"All {config.MAX_RETRIES} attempts failed for {url}"
                    )
                    return None

    # ── Save Raw Data ──────────────────────────────────────────
    def save_raw(self, rows: list[dict], city: str):
        """Save scraped rows to CSV in the raw data directory."""
        if not rows:
            self.logger.warning(f"No rows to save for {self.store_name} / {city}")
            return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.store_key}_{city.lower()}_{ts}.csv"
        filepath = os.path.join(config.RAW_DIR, filename)
        fieldnames = list(rows[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        self.logger.info(
            f"Saved {len(rows)} rows → {filepath}"
        )
        return filepath

    # ── Abstract Methods ───────────────────────────────────────
    @abc.abstractmethod
    def scrape_city(self, city: str) -> list[dict]:
        """Scrape all products for a given city. Must return list of dicts."""
        ...

    def run(self):
        """Run the scraper for all configured cities."""
        self.logger.info(
            f"=== Starting {self.store_name} scraper ==="
        )
        all_files = []
        total_rows = 0
        for city in self.cities:
            self.logger.info(f"--- Scraping {city} ---")
            try:
                rows = self.scrape_city(city)
                if rows:
                    filepath = self.save_raw(rows, city)
                    all_files.append(filepath)
                    total_rows += len(rows)
                    self.logger.info(
                        f"{city}: {len(rows)} products scraped"
                    )
                else:
                    self.logger.warning(f"{city}: No products returned")
            except Exception as e:
                self.logger.error(f"{city}: Scraper failed — {e}", exc_info=True)

        self.logger.info(
            f"=== {self.store_name} complete: {total_rows} total rows "
            f"across {len(all_files)} files ==="
        )
        return all_files
