"""
Data validation module — automated quality checks on cleaned data.
Checks: missing values, duplicates, unit consistency, outliers, price bounds.
"""
import os
import logging

import pandas as pd
import numpy as np

import config

logger = logging.getLogger("pipeline.validator")
logging.basicConfig(level=logging.INFO)


def check_missing_values(df: pd.DataFrame) -> dict:
    """Check missing value percentages per column."""
    missing = {}
    critical_cols = ["product_name", "price", "store", "city", "brand", "category"]
    for col in critical_cols:
        if col in df.columns:
            pct = (df[col].isna().sum() / len(df)) * 100
            status = "PASS" if pct <= config.MAX_MISSING_PCT else "FAIL"
            missing[col] = {"missing_pct": round(pct, 2), "status": status}
            if status == "FAIL":
                logger.warning(f"Missing values: {col} = {pct:.1f}% (threshold: {config.MAX_MISSING_PCT}%)")
    return missing


def check_duplicates(df: pd.DataFrame) -> dict:
    """Detect duplicate rows."""
    dedup_cols = ["product_name", "store", "city", "price", "size"]
    existing_cols = [c for c in dedup_cols if c in df.columns]
    dupes = df.duplicated(subset=existing_cols, keep=False).sum()
    total = len(df)
    pct = (dupes / total) * 100 if total > 0 else 0
    return {
        "duplicate_rows": int(dupes),
        "duplicate_pct": round(pct, 2),
        "status": "PASS" if pct < 5 else "WARN",
    }


def check_price_bounds(df: pd.DataFrame) -> dict:
    """Check prices are within sane bounds."""
    if "price" not in df.columns:
        return {"status": "SKIP"}
    below_min = (df["price"] < config.PRICE_MIN).sum()
    above_max = (df["price"] > config.PRICE_MAX).sum()
    return {
        "below_min": int(below_min),
        "above_max": int(above_max),
        "price_range": [float(df["price"].min()), float(df["price"].max())],
        "status": "PASS" if (below_min + above_max) == 0 else "WARN",
    }


def check_outliers(df: pd.DataFrame) -> dict:
    """Detect outliers using Z-score and IQR methods."""
    if "price" not in df.columns:
        return {"status": "SKIP"}

    # Z-score method
    mean = df["price"].mean()
    std = df["price"].std()
    if std > 0:
        z_scores = ((df["price"] - mean) / std).abs()
        z_outliers = (z_scores > config.OUTLIER_ZSCORE).sum()
    else:
        z_outliers = 0

    # IQR method
    q1 = df["price"].quantile(0.25)
    q3 = df["price"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    iqr_outliers = ((df["price"] < lower) | (df["price"] > upper)).sum()

    return {
        "z_score_outliers": int(z_outliers),
        "iqr_outliers": int(iqr_outliers),
        "z_score_pct": round((z_outliers / len(df)) * 100, 2),
        "iqr_pct": round((iqr_outliers / len(df)) * 100, 2),
        "iqr_bounds": [round(lower, 2), round(upper, 2)],
        "status": "PASS" if (z_outliers / len(df)) < 0.05 else "WARN",
    }


def check_unit_consistency(df: pd.DataFrame) -> dict:
    """Check that normalized units are consistent."""
    if "norm_unit" not in df.columns:
        return {"status": "SKIP"}
    unit_counts = df["norm_unit"].value_counts().to_dict()
    null_units = int(df["norm_unit"].isna().sum())
    return {
        "unit_distribution": unit_counts,
        "null_units": null_units,
        "null_unit_pct": round((null_units / len(df)) * 100, 2),
        "status": "PASS" if (null_units / len(df)) < 0.3 else "WARN",
    }


def check_store_distribution(df: pd.DataFrame) -> dict:
    """Check data distribution across stores and cities."""
    store_counts = df.groupby("store").size().to_dict()
    city_counts = df.groupby(["store", "city"]).size().to_dict()
    # Convert tuple keys to strings for JSON compatibility
    city_counts = {f"{k[0]}_{k[1]}": v for k, v in city_counts.items()}
    return {
        "store_counts": store_counts,
        "city_counts": city_counts,
        "num_stores": len(store_counts),
        "status": "PASS" if len(store_counts) >= 3 else "FAIL",
    }


def run_validation(df: pd.DataFrame = None) -> dict:
    """Run all validation checks. Returns full validation report."""
    if df is None:
        processed_path = os.path.join(config.PROCESSED_DIR, "all_products_cleaned.csv")
        if not os.path.exists(processed_path):
            logger.error("No cleaned data found. Run cleaner first.")
            return {}
        df = pd.read_csv(processed_path)

    logger.info(f"Running validation on {len(df)} rows...")

    report = {
        "total_rows": len(df),
        "missing_values": check_missing_values(df),
        "duplicates": check_duplicates(df),
        "price_bounds": check_price_bounds(df),
        "outliers": check_outliers(df),
        "unit_consistency": check_unit_consistency(df),
        "store_distribution": check_store_distribution(df),
    }

    # Overall pass/fail
    all_statuses = []
    for key, val in report.items():
        if isinstance(val, dict) and "status" in val:
            all_statuses.append(val["status"])
        elif isinstance(val, dict):
            for sub_val in val.values():
                if isinstance(sub_val, dict) and "status" in sub_val:
                    all_statuses.append(sub_val["status"])

    report["overall"] = "PASS" if "FAIL" not in all_statuses else "FAIL"

    # Log summary
    for check_name, result in report.items():
        if isinstance(result, dict) and "status" in result:
            logger.info(f"  {check_name}: {result['status']}")

    logger.info(f"Overall validation: {report['overall']}")

    # Save report
    import json
    report_path = os.path.join(config.PROCESSED_DIR, "validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Validation report saved → {report_path}")

    return report


if __name__ == "__main__":
    run_validation()
