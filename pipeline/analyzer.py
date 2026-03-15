"""
Statistical analysis module — computes all assignment-required metrics:
Product-level, Store-level, LDI, and Correlation analyses.
"""
import os
import logging

import pandas as pd
import numpy as np
from scipy import stats

import config

logger = logging.getLogger("pipeline.analyzer")
logging.basicConfig(level=logging.INFO)


# ═══════════════════════════════════════════════════════════════
# PRODUCT-LEVEL METRICS
# ═══════════════════════════════════════════════════════════════

def product_level_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-product price metrics across stores:
    Mean, Median, Std Dev, CV, Range, IQR, Price Spread Ratio,
    Relative Price Position Index (RPPI).
    """
    matched = df[df["match_id"] > 0].copy()
    if matched.empty:
        logger.warning("No matched products for product-level metrics")
        return pd.DataFrame()

    metrics = matched.groupby("match_id").agg(
        product_name=("product_name", "first"),
        brand=("brand", "first"),
        category=("category", "first"),
        stores_count=("store", "nunique"),
        cities_count=("city", "nunique"),
        mean_price=("price", "mean"),
        median_price=("price", "median"),
        std_price=("price", "std"),
        min_price=("price", "min"),
        max_price=("price", "max"),
        q1_price=("price", lambda x: x.quantile(0.25)),
        q3_price=("price", lambda x: x.quantile(0.75)),
    ).reset_index()

    # Coefficient of Variation
    metrics["cv"] = np.where(
        metrics["mean_price"] > 0,
        (metrics["std_price"] / metrics["mean_price"] * 100).round(2),
        0
    )

    # Price Range
    metrics["price_range"] = (metrics["max_price"] - metrics["min_price"]).round(2)

    # IQR
    metrics["iqr"] = (metrics["q3_price"] - metrics["q1_price"]).round(2)

    # Price Spread Ratio = max/min
    metrics["price_spread_ratio"] = np.where(
        metrics["min_price"] > 0,
        (metrics["max_price"] / metrics["min_price"]).round(3),
        0
    )

    # Round numeric columns
    for col in ["mean_price", "median_price", "std_price", "min_price",
                "max_price", "q1_price", "q3_price"]:
        metrics[col] = metrics[col].round(2)

    return metrics


def compute_rppi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Relative Price Position Index (RPPI) per store per product.
    RPPI = (store_price - min_price) / (max_price - min_price)
    Range: 0 (cheapest) to 1 (most expensive).
    """
    matched = df[df["match_id"] > 0].copy()
    if matched.empty:
        return pd.DataFrame()

    stats_df = matched.groupby("match_id").agg(
        min_price=("price", "min"),
        max_price=("price", "max"),
    ).reset_index()

    merged = matched.merge(stats_df, on="match_id", suffixes=("", "_agg"))
    # Since matched doesn't have min_price/max_price, the merged columns are just min_price and max_price
    price_range = merged["max_price"] - merged["min_price"]
    merged["rppi"] = np.where(
        price_range > 0,
        ((merged["price"] - merged["min_price"]) / price_range).round(4),
        0.5
    )
    return merged[["match_id", "product_name", "store", "city", "price", "rppi"]]


# ═══════════════════════════════════════════════════════════════
# STORE-LEVEL METRICS
# ═══════════════════════════════════════════════════════════════

def store_level_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate store-level metrics:
    - Avg category price index
    - Median deviation
    - Volatility score (avg CV within store)
    - Leadership frequency
    """
    matched = df[df["match_id"] > 0].copy()
    if matched.empty:
        return pd.DataFrame()

    # Price index: store's average price relative to overall average
    overall_avg = matched.groupby("match_id")["price"].mean()
    merged = matched.merge(
        overall_avg.rename("overall_avg"), on="match_id"
    )
    merged["price_index"] = merged["price"] / merged["overall_avg"]

    store_metrics = merged.groupby("store").agg(
        total_products=("product_name", "count"),
        unique_products=("match_id", "nunique"),
        avg_price=("price", "mean"),
        median_price=("price", "median"),
        avg_price_index=("price_index", "mean"),
        categories=("category", "nunique"),
        brands=("brand", "nunique"),
        cities=("city", "nunique"),
    ).round(3).reset_index()

    # Median deviation: median absolute deviation from median price
    for store in store_metrics["store"]:
        store_data = matched[matched["store"] == store]
        median_dev = (store_data["price"] - store_data["price"].median()).abs().median()
        store_metrics.loc[store_metrics["store"] == store, "median_deviation"] = round(median_dev, 2)

    # Volatility score: average CV of matched products within each store
    product_cv = matched.groupby(["store", "match_id"])["price"].agg(["mean", "std"])
    product_cv["cv"] = np.where(
        product_cv["mean"] > 0,
        product_cv["std"] / product_cv["mean"] * 100,
        0
    )
    vol = product_cv.groupby(level=0)["cv"].mean()
    for store in store_metrics["store"]:
        if store in vol.index:
            store_metrics.loc[store_metrics["store"] == store, "volatility_score"] = round(vol[store], 2)

    # Leadership frequency: how often is this store the cheapest?
    cheapest = matched.loc[matched.groupby("match_id")["price"].idxmin()]
    leadership = cheapest["store"].value_counts()
    total_matchids = matched["match_id"].nunique()
    for store in store_metrics["store"]:
        freq = leadership.get(store, 0)
        store_metrics.loc[store_metrics["store"] == store, "leadership_freq"] = freq
        store_metrics.loc[store_metrics["store"] == store, "leadership_pct"] = round(
            (freq / total_matchids) * 100 if total_matchids > 0 else 0, 1
        )

    return store_metrics


# ═══════════════════════════════════════════════════════════════
# LEADER DOMINANCE INDEX (LDI)
# ═══════════════════════════════════════════════════════════════

def compute_ldi(df: pd.DataFrame) -> dict:
    """
    Leader Dominance Index:
    - Standard LDI: % of products where one store is cheapest
    - Weighted LDI: LDI weighted by product value
    - Category-wise LDI: LDI broken down by category
    """
    matched = df[df["match_id"] > 0].copy()
    if matched.empty:
        return {}

    cheapest = matched.loc[matched.groupby("match_id")["price"].idxmin()]
    total = matched["match_id"].nunique()

    # Standard LDI per store
    standard_ldi = {}
    for store in matched["store"].unique():
        count = (cheapest["store"] == store).sum()
        standard_ldi[store] = round((count / total) * 100, 2) if total > 0 else 0

    # Weighted LDI (weighted by product value)
    cheapest_with_value = cheapest.copy()
    cheapest_with_value["value"] = cheapest_with_value["price"]
    total_value = cheapest_with_value["value"].sum()
    weighted_ldi = {}
    for store in matched["store"].unique():
        store_val = cheapest_with_value[cheapest_with_value["store"] == store]["value"].sum()
        weighted_ldi[store] = round((store_val / total_value) * 100, 2) if total_value > 0 else 0

    # Category-wise LDI
    category_ldi = {}
    for cat in matched["category"].unique():
        cat_data = matched[matched["category"] == cat]
        cat_cheapest = cat_data.loc[cat_data.groupby("match_id")["price"].idxmin()]
        cat_total = cat_data["match_id"].nunique()
        cat_ldi = {}
        for store in cat_data["store"].unique():
            count = (cat_cheapest["store"] == store).sum()
            cat_ldi[store] = round((count / cat_total) * 100, 2) if cat_total > 0 else 0
        category_ldi[cat] = cat_ldi

    return {
        "standard_ldi": standard_ldi,
        "weighted_ldi": weighted_ldi,
        "category_ldi": category_ldi,
    }


# ═══════════════════════════════════════════════════════════════
# CORRELATIONS & COMPETITION
# ═══════════════════════════════════════════════════════════════

def correlation_analysis(df: pd.DataFrame, product_metrics: pd.DataFrame) -> dict:
    """
    Correlation analyses:
    - Product size vs price dispersion
    - Number of competitors vs spread
    - Brand tier vs volatility
    - City correlation matrix
    - Cross-store price synchronization
    """
    results = {}

    # 1. Size vs Dispersion
    if "norm_value" in product_metrics.columns or "norm_value" in df.columns:
        merged = df[df["match_id"] > 0].copy()
        size_disp = merged.groupby("match_id").agg(
            norm_value=("norm_value", "first"),
            price_cv=("price", lambda x: (x.std() / x.mean() * 100) if x.mean() > 0 else 0),
        ).dropna()
        if len(size_disp) > 5:
            corr, pval = stats.pearsonr(
                size_disp["norm_value"].fillna(0), size_disp["price_cv"]
            )
            results["size_vs_dispersion"] = {
                "correlation": round(corr, 4),
                "p_value": round(pval, 4),
                "interpretation": "Larger products tend to have "
                + ("higher" if corr > 0 else "lower")
                + f" price dispersion (r={corr:.3f}, p={pval:.4f})"
            }

    # 2. Competitors (stores count) vs Spread
    if not product_metrics.empty and "stores_count" in product_metrics.columns:
        valid = product_metrics[product_metrics["price_range"] > 0]
        if len(valid) > 5:
            corr, pval = stats.pearsonr(
                valid["stores_count"], valid["price_range"]
            )
            results["competitors_vs_spread"] = {
                "correlation": round(corr, 4),
                "p_value": round(pval, 4),
            }

    # 3. City correlation matrix
    matched = df[df["match_id"] > 0].copy()
    city_pivot = matched.pivot_table(
        values="price", index="match_id", columns="city", aggfunc="mean"
    ).dropna(axis=1, how="all")

    if city_pivot.shape[1] >= 2:
        city_corr = city_pivot.corr().round(4)
        results["city_correlation_matrix"] = city_corr.to_dict()

    # 4. Cross-store price synchronization
    store_pivot = matched.pivot_table(
        values="price", index="match_id", columns="store", aggfunc="mean"
    ).dropna()
    if store_pivot.shape[1] >= 2:
        store_corr = store_pivot.corr().round(4)
        results["cross_store_synchronization"] = store_corr.to_dict()

    # 5. Brand tier vs volatility
    brand_stats = matched.groupby("brand").agg(
        avg_price=("price", "mean"),
        price_volatility=("price", "std"),
    ).dropna()
    if len(brand_stats) > 5:
        corr, pval = stats.pearsonr(
            brand_stats["avg_price"], brand_stats["price_volatility"]
        )
        results["brand_tier_vs_volatility"] = {
            "correlation": round(corr, 4),
            "p_value": round(pval, 4),
        }

    return results


# ═══════════════════════════════════════════════════════════════
# MAIN ANALYSIS RUNNER
# ═══════════════════════════════════════════════════════════════

def run_analysis():
    """Run all analyses and save results."""
    import json

    matched_path = os.path.join(config.MATCHED_DIR, "matched_products.csv")
    if not os.path.exists(matched_path):
        logger.error("Matched data not found. Run matcher first.")
        return {}

    df = pd.read_csv(matched_path, low_memory=False)
    logger.info(f"Loaded {len(df)} rows for analysis ({(df['match_id'] > 0).sum()} matched)")

    results = {}

    # Product-level metrics
    logger.info("Computing product-level metrics...")
    prod_metrics = product_level_metrics(df)
    if not prod_metrics.empty:
        prod_path = os.path.join(config.MATCHED_DIR, "product_metrics.csv")
        prod_metrics.to_csv(prod_path, index=False)
        results["product_metrics_count"] = len(prod_metrics)
        logger.info(f"Product metrics: {len(prod_metrics)} match groups → {prod_path}")

    # RPPI
    logger.info("Computing RPPI...")
    rppi = compute_rppi(df)
    if not rppi.empty:
        rppi_path = os.path.join(config.MATCHED_DIR, "rppi.csv")
        rppi.to_csv(rppi_path, index=False)
        results["rppi_count"] = len(rppi)

    # Store-level metrics
    logger.info("Computing store-level metrics...")
    store_metrics = store_level_metrics(df)
    if not store_metrics.empty:
        store_path = os.path.join(config.MATCHED_DIR, "store_metrics.csv")
        store_metrics.to_csv(store_path, index=False)
        results["store_metrics"] = store_metrics.to_dict(orient="records")

    # LDI
    logger.info("Computing LDI...")
    ldi = compute_ldi(df)
    results["ldi"] = ldi

    # Correlations
    logger.info("Computing correlations...")
    corr = correlation_analysis(df, prod_metrics)
    results["correlations"] = corr

    # Save full analysis results
    analysis_path = os.path.join(config.MATCHED_DIR, "analysis_results.json")
    with open(analysis_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Full analysis results → {analysis_path}")

    logger.info("=== Analysis Complete ===")
    return results


if __name__ == "__main__":
    run_analysis()
