"""
Al-Fatah scraper using the Shopify JSON API.
Endpoint: alfatah.pk/products.json?page=N&limit=250

Al-Fatah is Shopify-based, so we can paginate through all products
via the public products.json endpoint. Each page returns up to 250 products.
Products are tagged with categories, brands, and barcodes.
"""
import re
from datetime import datetime

from scrapers.base_scraper import BaseScraper


class AlFatahScraper(BaseScraper):
    """Scrape Al-Fatah product catalog via Shopify JSON API."""

    def __init__(self):
        super().__init__("alfatah")
        self.products_per_page = 250

    def _extract_brand(self, title: str, tags: list) -> str:
        """Extract brand name from tags (B_ prefix) or product title."""
        for tag in tags:
            if tag.startswith("B_"):
                return tag[2:].strip()
        # Fallback: first word of title if it looks like a brand
        words = title.split()
        if words:
            return words[0].strip()
        return "Unknown"

    def _extract_category(self, tags: list) -> str:
        """Extract primary category from product tags."""
        priority_categories = [
            "Dairy", "Beverages", "Snacks & Confectioneries",
            "Snacks & Beverages", "Breakfast", "Cooking Ingredients",
            "Personal Care", "Household & Cleaning Products",
            "Baby & Maternity Care", "Frozen Food", "Grocery Food",
            "Grocery Non Food", "Hair Care", "Skin Care", "Oral Care",
            "Chips & Savories", "Tea & Coffee", "Spices & Dressings",
            "Oil & Ghee", "Noodles & Pasta", "Cleaning Products",
            "Toys", "Electronics", "Crockery", "House Hold",
            "Ladies Shoes & Bags", "Kids Wear", "Perfume",
        ]
        for cat in priority_categories:
            for tag in tags:
                if cat.lower() in tag.lower():
                    return cat
        # Fallback to product_type or first meaningful tag
        for tag in tags:
            if tag not in ("Alfatah", "New Arrival", "Not", "Non", "Grocery"):
                if not tag.startswith("Barcode_"):
                    return tag
        return "Uncategorized"

    def _extract_size(self, title: str) -> str:
        """Extract product size/quantity from title using regex."""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(ML|ml|Ml|L|l|KG|kg|Kg|G|g|GM|gm|Gm|'
            r'OZ|oz|LTR|ltr|Ltr|PCS|pcs|Pcs|PC|pc|PACK|pack|Pack|'
            r'SHEETS|sheets|ROLLS|rolls|SACHET|sachet|TABS|tabs)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return f"{match.group(1)}{match.group(2).upper()}"
        # Try "Pack of N"
        pack_match = re.search(r'Pack\s+of\s+(\d+)', title, re.IGNORECASE)
        if pack_match:
            return f"{pack_match.group(1)}PCS"
        return ""

    def _parse_product(self, product: dict, city: str) -> list[dict]:
        """Parse a single Shopify product JSON into row dict(s)."""
        rows = []
        title = product.get("title", "").strip()
        tags = product.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        vendor = product.get("vendor", "")
        product_type = product.get("product_type", "")
        created_at = product.get("published_at", "")
        brand = self._extract_brand(title, tags)
        category = self._extract_category(tags)
        size = self._extract_size(title)

        for variant in product.get("variants", []):
            price_str = variant.get("price", "0")
            compare_price_str = variant.get("compare_at_price", "0") or "0"
            try:
                price = float(price_str)
            except (ValueError, TypeError):
                price = 0.0
            try:
                original_price = float(compare_price_str)
            except (ValueError, TypeError):
                original_price = price

            if price <= 0:
                continue

            row = {
                "product_id": str(product.get("id", "")),
                "product_name": title,
                "variant_title": variant.get("title", "Default Title"),
                "sku": variant.get("sku", ""),
                "price": price,
                "original_price": original_price,
                "brand": brand,
                "category": category,
                "size": size,
                "tags": "|".join(tags) if isinstance(tags, list) else tags,
                "vendor": vendor,
                "product_type": product_type,
                "available": variant.get("available", False),
                "image_url": (
                    product["images"][0]["src"]
                    if product.get("images") else ""
                ),
                "store": self.store_name,
                "city": city,
                "scraped_at": datetime.now().isoformat(),
            }
            rows.append(row)
        return rows

    def scrape_city(self, city: str) -> list[dict]:
        """
        Scrape all products from Al-Fatah for a given city.
        Al-Fatah is a single Shopify store so the full catalog applies
        to all cities; we tag each row with the city for analysis.
        """
        all_rows = []
        page = 1
        max_pages = 100  # Shopify limits to 100 pages max

        while page <= max_pages:
            self.logger.info(
                f"[{city}] Fetching page {page} "
                f"(limit={self.products_per_page})..."
            )
            resp = self.request_with_retry(
                self.store_cfg["api_url"],
                params={"page": page, "limit": self.products_per_page},
            )
            if resp is None:
                self.logger.info(f"[{city}] End of pagination at page {page}")
                break

            try:
                data = resp.json()
            except Exception as e:
                self.logger.error(f"[{city}] JSON parse error on page {page}: {e}")
                break

            products = data.get("products", [])
            if not products:
                self.logger.info(
                    f"[{city}] No more products at page {page}. Done."
                )
                break

            for product in products:
                rows = self._parse_product(product, city)
                all_rows.extend(rows)

            self.logger.info(
                f"[{city}] Page {page}: {len(products)} products "
                f"→ {len(all_rows)} total rows"
            )
            page += 1

        return all_rows


# ── CLI entry point ───────────────────────────────────────────
if __name__ == "__main__":
    scraper = AlFatahScraper()
    scraper.run()
