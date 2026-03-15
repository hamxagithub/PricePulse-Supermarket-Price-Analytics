"""
Data cleaning and normalization pipeline.
Handles: unit standardization, brand extraction, size parsing,
price-per-unit calculation, deduplication, and missing value handling.
"""
import os
import re
import glob
import logging

import pandas as pd
import numpy as np

import config

logger = logging.getLogger("pipeline.cleaner")
logging.basicConfig(level=logging.INFO)


# ── Unit Normalization ─────────────────────────────────────────
UNIT_MAP = {
    "ML": "ML", "ml": "ML", "Ml": "ML",
    "L": "ML", "l": "ML", "LTR": "ML", "ltr": "ML", "Ltr": "ML",
    "G": "G", "g": "G", "GM": "G", "gm": "G", "Gm": "G", "GRM": "G",
    "KG": "G", "kg": "G", "Kg": "G",
    "OZ": "ML",
    "PCS": "PCS", "pcs": "PCS", "Pcs": "PCS",
    "PC": "PCS", "pc": "PCS",
    "PACK": "PCS", "pack": "PCS", "Pack": "PCS",
    "SHEETS": "PCS", "sheets": "PCS",
    "ROLLS": "PCS", "rolls": "PCS",
    "SACHET": "PCS", "sachet": "PCS",
    "TABS": "PCS", "tabs": "PCS",
}

CONVERSION_FACTORS = {
    ("L", "ML"): 1000, ("l", "ML"): 1000,
    ("LTR", "ML"): 1000, ("ltr", "ML"): 1000, ("Ltr", "ML"): 1000,
    ("KG", "G"): 1000, ("kg", "G"): 1000, ("Kg", "G"): 1000,
    ("OZ", "ML"): 29.5735,
}


def normalize_unit(value: float, unit: str) -> tuple:
    """Convert a value+unit to normalized (value, standard_unit)."""
    std_unit = UNIT_MAP.get(unit, unit.upper())
    factor = CONVERSION_FACTORS.get((unit, std_unit), 1.0)
    return round(value * factor, 2), std_unit


def extract_size_info(size_str: str) -> tuple:
    """Extract numeric value and unit from size string like '500ML'."""
    if not size_str or pd.isna(size_str):
        return None, None
    match = re.match(r'(\d+(?:\.\d+)?)\s*(.*)', str(size_str).strip())
    if match:
        value = float(match.group(1))
        unit = match.group(2).strip()
        if unit:
            return normalize_unit(value, unit)
    return None, None


def compute_price_per_unit(price, norm_value, norm_unit):
    """Compute price per standard unit (per ML, per G, per PCS)."""
    if price and norm_value and norm_value > 0:
        return round(price / norm_value, 4)
    return None


def clean_brand(brand: str) -> str:
    """Normalize brand name."""
    if not brand or pd.isna(brand):
        return "Unknown"
    brand = str(brand).strip()
    brand = re.sub(r'[^a-zA-Z0-9\s&\'-]', '', brand)
    # Title case
    brand = brand.title()
    # Common brand normalization
    brand_map = {
        "K&N'S": "K&Ns", "K&N": "K&Ns", "Kns": "K&Ns",
        "Coca Cola": "Coca-Cola", "Cocacola": "Coca-Cola",
        "Head And Shoulders": "Head & Shoulders",
        "Surf": "Surf Excel",
        "Milkpak": "MilkPak", "Milk Pak": "MilkPak",
        "Dairy Omung": "Omung",
    }
    for pattern, replacement in brand_map.items():
        if brand.lower() == pattern.lower():
            return replacement
    return brand


def clean_product_name(name: str) -> str:
    """Clean and standardize product name."""
    if not name or pd.isna(name):
        return ""
    name = str(name).strip()
    # Remove excessive whitespace
    name = re.sub(r'\s+', ' ', name)
    # Remove special unicode characters
    name = name.encode('ascii', 'ignore').decode('ascii')
    return name.strip()


# ── Main Cleaning Pipeline ────────────────────────────────────
def load_raw_data() -> pd.DataFrame:
    """Load all raw CSV files from data/raw/ into a single DataFrame."""
    raw_files = glob.glob(os.path.join(config.RAW_DIR, "*.csv"))
    if not raw_files:
        logger.warning("No raw CSV files found in data/raw/")
        return pd.DataFrame()

    dfs = []
    for f in raw_files:
        try:
            df = pd.read_csv(f, encoding="utf-8")
            logger.info(f"Loaded {len(df)} rows from {os.path.basename(f)}")
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {f}: {e}")

    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total raw rows loaded: {len(combined)}")
    return combined


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning steps to the DataFrame."""
    if df.empty:
        return df

    logger.info("Starting data cleaning pipeline...")
    initial_count = len(df)

    # 1. Clean product names
    df["product_name"] = df["product_name"].apply(clean_product_name)

    # 2. Clean and normalize brands
    df["brand"] = df["brand"].apply(clean_brand)

    # 3. Ensure numeric prices
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["original_price"] = pd.to_numeric(df["original_price"], errors="coerce")

    # 4. Remove rows with invalid prices
    df = df[df["price"] > 0].copy()
    df["original_price"] = df["original_price"].fillna(df["price"])

    # 5. Compute discount percentage
    df["discount_pct"] = np.where(
        df["original_price"] > df["price"],
        ((df["original_price"] - df["price"]) / df["original_price"] * 100).round(1),
        0.0
    )

    # 6. Parse and normalize sizes
    size_data = df["size"].apply(extract_size_info)
    df["norm_value"] = size_data.apply(lambda x: x[0] if x else None)
    df["norm_unit"] = size_data.apply(lambda x: x[1] if x else None)

    # 7. Compute price per unit
    df["price_per_unit"] = df.apply(
        lambda row: compute_price_per_unit(
            row["price"], row["norm_value"], row["norm_unit"]
        ),
        axis=1,
    )

    # 8. Standardize city names
    df["city"] = df["city"].str.strip().str.title()

    # 9. Standardize store names
    df["store"] = df["store"].str.strip()

    # 10. Standardize categories
    df["category"] = df["category"].str.strip().str.title()

    # 11. Remove exact duplicates
    dedup_cols = ["product_name", "store", "city", "price", "size"]
    before_dedup = len(df)
    df = df.drop_duplicates(subset=dedup_cols, keep="first")
    logger.info(f"Deduplication: {before_dedup} → {len(df)} rows "
                f"(removed {before_dedup - len(df)} duplicates)")

    # 12. Price sanity bounds
    df = df[
        (df["price"] >= config.PRICE_MIN) &
        (df["price"] <= config.PRICE_MAX)
    ].copy()

    logger.info(f"Cleaning complete: {initial_count} → {len(df)} rows")
    return df


def run_cleaning():
    """Full cleaning pipeline: load raw → clean → save processed."""
    df = load_raw_data()
    if df.empty:
        logger.error("No data to clean. Run scrapers first.")
        return None

    cleaned = clean_dataframe(df)

    # Save processed data
    output_path = os.path.join(config.PROCESSED_DIR, "all_products_cleaned.csv")
    cleaned.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Saved cleaned data: {len(cleaned)} rows → {output_path}")

    # Save per-store summary
    summary = cleaned.groupby(["store", "city"]).agg(
        products=("product_name", "count"),
        avg_price=("price", "mean"),
        brands=("brand", "nunique"),
        categories=("category", "nunique"),
    ).round(2)
    summary_path = os.path.join(config.PROCESSED_DIR, "store_city_summary.csv")
    summary.to_csv(summary_path)
    logger.info(f"Saved store-city summary → {summary_path}")

    return cleaned


if __name__ == "__main__":
    run_cleaning()
