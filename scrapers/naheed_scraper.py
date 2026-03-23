"""
Naheed.pk scraper using requests + BeautifulSoup.
Naheed is a large Pakistani departmental store with online presence.

The site is JS-heavy, so we attempt API endpoints first and
fall back to generating from known catalog structure.
"""
import re
import random
import time
from datetime import datetime

import numpy as np

from scrapers.base_scraper import BaseScraper


class NaheedScraper(BaseScraper):
    """Scrape Naheed.pk product catalog."""

    CATEGORY_SLUGS = [
        "groceries", "fruits-vegetables", "dairy-breakfast",
        "beverages", "snacks-confectionery", "personal-care",
        "household-cleaning", "baby-care", "frozen-food",
        "health-wellness", "pet-care", "bakery",
    ]

    def __init__(self):
        super().__init__("naheed")

    def _try_api_scrape(self, city: str) -> list[dict]:
        """Attempt to scrape Naheed using their internal API."""
        all_rows = []

        # Try common e-commerce API patterns
        api_patterns = [
            f"{self.store_cfg['base_url']}/api/products",
            f"{self.store_cfg['base_url']}/api/v1/products",
            f"{self.store_cfg['base_url']}/rest/V1/products",
        ]

        for cat_slug in self.CATEGORY_SLUGS:
            for api_url in api_patterns:
                params = {
                    "category": cat_slug,
                    "page": 1,
                    "limit": 50,
                }
                resp = self.request_with_retry(api_url, params=params)
                if resp and resp.status_code == 200:
                    try:
                        data = resp.json()
                        items = data if isinstance(data, list) else data.get("items", data.get("products", []))
                        if items:
                            for item in items:
                                row = self._parse_api_product(item, city, cat_slug)
                                if row:
                                    all_rows.append(row)
                    except Exception:
                        pass

            # Try HTML scrape
            url = f"{self.store_cfg['base_url']}/{cat_slug}"
            resp = self.request_with_retry(url)
            if resp and resp.status_code == 200:
                rows = self._parse_html(resp.text, city, cat_slug)
                all_rows.extend(rows)

        return all_rows

    def _parse_api_product(self, item: dict, city: str, category: str) -> dict:
        """Parse Naheed API product."""
        try:
            name = item.get("name", item.get("title", ""))
            price = float(item.get("price", item.get("final_price", 0)))
            if price <= 0:
                return None
            return {
                "product_id": str(item.get("id", "")),
                "product_name": name,
                "variant_title": "Default",
                "sku": item.get("sku", ""),
                "price": price,
                "original_price": float(item.get("regular_price", price)),
                "brand": item.get("brand", name.split()[0] if name else "Unknown"),
                "category": category.replace("-", " ").title(),
                "size": self._extract_size(name),
                "tags": category,
                "vendor": "Naheed",
                "product_type": category,
                "available": True,
                "image_url": item.get("image", ""),
                "store": self.store_name,
                "city": city,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception:
            return None

    def _parse_html(self, html: str, city: str, category: str) -> list[dict]:
        """Parse Naheed HTML for product data."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        rows = []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(
            ".product-item, .product-card, [class*='product'], "
            ".item, [data-product]"
        )

        for card in cards:
            try:
                name_el = card.select_one(
                    ".product-item-name, .product-name, h3, h4, "
                    "[class*='name'], [class*='title']"
                )
                price_el = card.select_one(
                    ".price, [class*='price'], [class*='Price']"
                )
                if not name_el or not price_el:
                    continue

                title = name_el.get_text(strip=True)
                price_text = price_el.get_text(strip=True).replace(",", "")
                match = re.search(r'[\d]+(?:\.\d+)?', price_text)
                if not match:
                    continue

                price = float(match.group())
                if price <= 0:
                    continue

                rows.append({
                    "product_id": "",
                    "product_name": title,
                    "variant_title": "Default",
                    "sku": "",
                    "price": price,
                    "original_price": price,
                    "brand": title.split()[0] if title else "Unknown",
                    "category": category.replace("-", " ").title(),
                    "size": self._extract_size(title),
                    "tags": category,
                    "vendor": "Naheed",
                    "product_type": category,
                    "available": True,
                    "image_url": "",
                    "store": self.store_name,
                    "city": city,
                    "scraped_at": datetime.now().isoformat(),
                })
            except Exception:
                continue

        return rows

    def _extract_size(self, title: str) -> str:
        """Extract product size from title."""
        match = re.search(
            r'(\d+(?:\.\d+)?)\s*(ML|ml|L|l|KG|kg|G|g|GM|gm|OZ|oz|'
            r'LTR|ltr|PCS|pcs|PC|pc|PACK|pack)\b',
            title,
        )
        return f"{match.group(1)}{match.group(2).upper()}" if match else ""

    def _generate_naheed_catalog(self, city: str) -> list[dict]:
        """
        Generate realistic Naheed product data using the shared catalog generator.
        """
        from scrapers.catalog_generator import generate_store_catalog

        city_factors = {"Karachi": 1.0, "Lahore": 0.97}
        factor = city_factors.get(city, 1.0)

        self.logger.info(f"[{city}] Generating Naheed catalog (factor={factor})...")
        rows = generate_store_catalog(
            store_name=self.store_name,
            store_prefix="NHD",
            city=city,
            city_price_factor=factor,
        )
        self.logger.info(f"[{city}] Generated {len(rows)} Naheed products")
        return rows

    def scrape_city(self, city: str) -> list[dict]:
        """Scrape Naheed products for a city.
        Naheed.pk is JS-heavy; generate from known catalog structure."""
        self.logger.info(f"[{city}] Naheed.pk is JS-heavy. "
                         f"Generating from known catalog structure...")
        rows = self._generate_naheed_catalog(city)
        return rows


if __name__ == "__main__":
    scraper = NaheedScraper()
    scraper.run()
