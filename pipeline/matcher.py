"""
Entity Resolution / Product Matching Pipeline.
Matches products across different stores using:
1. Deterministic matching (exact brand + normalized size key)
2. Fuzzy matching (token sort ratio ≥ threshold)

Outputs matched_products.csv with match_id column for cross-store analysis.
"""
import os
import re
import logging
from collections import defaultdict

import pandas as pd
import numpy as np

try:
    from rapidfuzz import fuzz, process
except ImportError:
    from difflib import SequenceMatcher

    class fuzz:
        @staticmethod
        def token_sort_ratio(a, b):
            return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100

import config

logger = logging.getLogger("pipeline.matcher")
logging.basicConfig(level=logging.INFO)

# Stopwords to remove when building matching keys
STOPWORDS = {
    "the", "a", "an", "of", "and", "in", "for", "with", "without",
    "pack", "packet", "box", "bottle", "jar", "can", "tin", "tube",
    "bag", "pouch", "sachet", "piece", "roll", "sheet", "pair",
    "premium", "special", "new", "original", "classic", "regular",
    "imported", "local", "fresh", "pure", "natural", "organic",
    "extra", "super", "mega", "mini", "small", "medium", "large",
    "family", "economy", "value",
}


def clean_token(name: str) -> str:
    """Clean product name for matching: lowercase, remove punctuation/stopwords."""
    if not name or pd.isna(name):
        return ""
    name = str(name).lower().strip()
    # Remove common unit patterns (we use normalized size separately)
    name = re.sub(r'\d+(?:\.\d+)?\s*(ml|l|ltr|g|gm|kg|oz|pcs|pc|pack)\b', '', name)
    # Remove punctuation
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    # Remove stopwords
    tokens = [t for t in name.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(sorted(tokens))


def build_match_key(row) -> str:
    """Build a deterministic matching key from brand + cleaned name + size."""
    brand = str(row.get("brand", "")).lower().strip()
    cleaned_name = clean_token(row.get("product_name", ""))
    norm_value = row.get("norm_value", "")
    norm_unit = row.get("norm_unit", "")

    size_part = ""
    if norm_value and not pd.isna(norm_value):
        size_part = f"{float(norm_value):.0f}{norm_unit}"

    return f"{brand}|{cleaned_name}|{size_part}"


def deterministic_match(df: pd.DataFrame) -> pd.DataFrame:
    """
    Phase 1: Match products with identical match keys across stores.
    Only matches products that appear in 2+ stores.
    """
    logger.info("Phase 1: Deterministic matching...")

    df["match_key"] = df.apply(build_match_key, axis=1)

    # Group by match key and find cross-store matches
    match_groups = defaultdict(list)
    for idx, row in df.iterrows():
        match_groups[row["match_key"]].append((idx, row["store"]))

    match_id = 0
    match_ids = {}

    for key, entries in match_groups.items():
        stores = set(e[1] for e in entries)
        if len(stores) >= 2:  # Cross-store match
            match_id += 1
            for idx, _ in entries:
                match_ids[idx] = match_id

    df["match_id"] = df.index.map(lambda x: match_ids.get(x, 0))

    matched_count = (df["match_id"] > 0).sum()
    unique_matches = df[df["match_id"] > 0]["match_id"].nunique()
    logger.info(
        f"Deterministic: {unique_matches} unique match groups, "
        f"{matched_count} total matched rows"
    )
    return df


def fuzzy_match(df: pd.DataFrame) -> pd.DataFrame:
    """
    Phase 2: Fuzzy match unmatched products across stores.
    Uses token sort ratio to find similar product names.
    """
    logger.info("Phase 2: Fuzzy matching...")

    max_match_id = df["match_id"].max()
    if pd.isna(max_match_id):
        max_match_id = 0
    next_match_id = int(max_match_id) + 1

    unmatched = df[df["match_id"] == 0].copy()
    matched_count = 0

    # Group unmatched products by category for efficiency
    for category in unmatched["category"].unique():
        cat_products = unmatched[unmatched["category"] == category]

        # Get products per store
        stores = cat_products["store"].unique()
        if len(stores) < 2:
            continue

        # Compare products between store pairs
        for i, store_a in enumerate(stores):
            for store_b in stores[i + 1:]:
                products_a = cat_products[cat_products["store"] == store_a]
                products_b = cat_products[cat_products["store"] == store_b]

                for idx_a, row_a in products_a.iterrows():
                    if df.at[idx_a, "match_id"] > 0:
                        continue  # Already matched

                    clean_a = clean_token(row_a["product_name"])
                    if not clean_a:
                        continue

                    best_score = 0
                    best_idx = None

                    for idx_b, row_b in products_b.iterrows():
                        if df.at[idx_b, "match_id"] > 0:
                            continue

                        clean_b = clean_token(row_b["product_name"])
                        if not clean_b:
                            continue

                        # Check same brand
                        if (row_a["brand"].lower() != row_b["brand"].lower()):
                            continue

                        score = fuzz.token_sort_ratio(clean_a, clean_b)
                        if score > best_score:
                            best_score = score
                            best_idx = idx_b

                    if best_score >= config.FUZZY_MATCH_THRESHOLD and best_idx is not None:
                        # Assign same match ID
                        if df.at[idx_a, "match_id"] > 0:
                            mid = df.at[idx_a, "match_id"]
                        else:
                            mid = next_match_id
                            next_match_id += 1

                        df.at[idx_a, "match_id"] = mid
                        df.at[best_idx, "match_id"] = mid
                        matched_count += 1

    new_matches = df[df["match_id"] > max_match_id]["match_id"].nunique()
    logger.info(f"Fuzzy: {new_matches} additional match groups found")
    return df


def run_matching():
    """Full matching pipeline: load processed → match → save."""
    processed_path = os.path.join(config.PROCESSED_DIR, "all_products_cleaned.csv")
    if not os.path.exists(processed_path):
        logger.error(f"Cleaned data not found at {processed_path}. Run cleaner first.")
        return None

    df = pd.read_csv(processed_path)
    logger.info(f"Loaded {len(df)} cleaned products for matching")

    # Phase 1: Deterministic matching
    df = deterministic_match(df)

    # Phase 2: Fuzzy matching for remaining products
    df = fuzzy_match(df)

    # Save matched products
    output_path = os.path.join(config.MATCHED_DIR, "matched_products.csv")
    df.to_csv(output_path, index=False, encoding="utf-8")

    total_matched = (df["match_id"] > 0).sum()
    unique_groups = df[df["match_id"] > 0]["match_id"].nunique()

    logger.info(f"=== Matching Complete ===")
    logger.info(f"Total matched rows: {total_matched}")
    logger.info(f"Unique match groups: {unique_groups}")
    logger.info(f"Saved → {output_path}")

    # Save match summary
    if total_matched > 0:
        match_summary = (
            df[df["match_id"] > 0]
            .groupby("match_id")
            .agg(
                stores=("store", lambda x: "|".join(sorted(x.unique()))),
                products=("product_name", "first"),
                avg_price=("price", "mean"),
                price_range=("price", lambda x: x.max() - x.min()),
                cities=("city", lambda x: "|".join(sorted(x.unique()))),
            )
            .round(2)
        )
        summary_path = os.path.join(config.MATCHED_DIR, "match_summary.csv")
        match_summary.to_csv(summary_path)
        logger.info(f"Match summary saved → {summary_path}")

    return df


if __name__ == "__main__":
    run_matching()
