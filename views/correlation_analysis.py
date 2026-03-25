"""
Correlation & Competition Analysis Page —
Scatter plots, heatmaps, and correlation statistics.
"""
import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

import config
from styles.theme import styled_plotly, PLOTLY_COLORS


def render():
    st.markdown("# 🔗 Correlation & Competition Analysis")
    st.markdown("Statistical relationships between pricing variables across stores and cities")

    analysis_path = os.path.join(config.MATCHED_DIR, "analysis_results.json")
    matched_path = os.path.join(config.MATCHED_DIR, "matched_products.csv")
    metrics_path = os.path.join(config.MATCHED_DIR, "product_metrics.csv")

    if not os.path.exists(analysis_path):
        st.warning("⚠️ Analysis results not found. Run the analysis pipeline first.")
        return

    with open(analysis_path) as f:
        analysis = json.load(f)

    corr = analysis.get("correlations", {})
    matched = pd.read_csv(matched_path, low_memory=False) if os.path.exists(matched_path) else pd.DataFrame()
    metrics = pd.read_csv(metrics_path) if os.path.exists(metrics_path) else pd.DataFrame()

    # ── Correlation Summary Cards ──────────────────────────
    st.markdown("### Key Correlations")
    tabs = st.tabs([
        "Size vs Dispersion",
        "Competitors vs Spread",
        "Brand Tier vs Volatility",
        "City Correlation",
        "Cross-Store Sync",
    ])

    # Tab 1: Size vs Dispersion
    with tabs[0]:
        data = corr.get("size_vs_dispersion", {})
        if data:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Pearson Correlation", f"{data.get('correlation', 0):.4f}")
                st.metric("P-value", f"{data.get('p_value', 0):.4f}")
            with c2:
                st.info(data.get("interpretation", "No interpretation available"))

            # Scatter plot
            if not matched.empty and "norm_value" in matched.columns:
                m = matched[matched["match_id"] > 0].copy()
                size_cv = m.groupby("match_id").agg(
                    norm_value=("norm_value", "first"),
                    cv=("price", lambda x: (x.std() / x.mean() * 100) if x.mean() > 0 else 0),
                    product_name=("product_name", "first"),
                ).dropna()

                fig = px.scatter(
                    size_cv, x="norm_value", y="cv",
                    hover_data=["product_name"],
                    color_discrete_sequence=[PLOTLY_COLORS[0]],
                    labels={"norm_value": "Normalized Size", "cv": "Price CV (%)"},
                    trendline="ols",
                )
                fig = styled_plotly(fig)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Size vs Dispersion data not available")

    # Tab 2: Competitors vs Spread
    with tabs[1]:
        data = corr.get("competitors_vs_spread", {})
        if data:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Pearson Correlation", f"{data.get('correlation', 0):.4f}")
            with c2:
                st.metric("P-value", f"{data.get('p_value', 0):.4f}")

            if not metrics.empty:
                fig = px.scatter(
                    metrics, x="stores_count", y="price_range",
                    color="category",
                    hover_data=["product_name"],
                    color_discrete_sequence=PLOTLY_COLORS,
                    labels={"stores_count": "# of Stores", "price_range": "Price Range (PKR)"},
                )
                fig = styled_plotly(fig)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Competitors vs Spread data not available")

    # Tab 3: Brand Tier vs Volatility
    with tabs[2]:
        data = corr.get("brand_tier_vs_volatility", {})
        if data:
            st.metric("Pearson Correlation", f"{data.get('correlation', 0):.4f}")
            st.metric("P-value", f"{data.get('p_value', 0):.4f}")

            if not matched.empty:
                brand_stats = matched.groupby("brand").agg(
                    avg_price=("price", "mean"),
                    volatility=("price", "std"),
                    products=("product_name", "count"),
                ).dropna().reset_index()
                brand_stats = brand_stats[brand_stats["products"] >= 3]

                fig = px.scatter(
                    brand_stats, x="avg_price", y="volatility",
                    size="products", hover_data=["brand"],
                    color_discrete_sequence=[PLOTLY_COLORS[2]],
                    labels={"avg_price": "Avg Price (PKR)", "volatility": "Price Std Dev"},
                    trendline="ols",
                )
                fig = styled_plotly(fig)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Brand tier vs volatility data not available")

    # Tab 4: City Correlation Matrix
    with tabs[3]:
        city_corr = corr.get("city_correlation_matrix", {})
        if city_corr:
            city_df = pd.DataFrame(city_corr)
            fig = px.imshow(
                city_df, text_auto=".3f",
                color_continuous_scale="RdBu_r",
                labels={"x": "City", "y": "City", "color": "Correlation"},
                zmin=-1, zmax=1,
            )
            fig = styled_plotly(fig)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("City correlation matrix not available")

    # Tab 5: Cross-Store Synchronization
    with tabs[4]:
        store_sync = corr.get("cross_store_synchronization", {})
        if store_sync:
            sync_df = pd.DataFrame(store_sync)
            fig = px.imshow(
                sync_df, text_auto=".3f",
                color_continuous_scale="Viridis",
                labels={"x": "Store", "y": "Store", "color": "Price Correlation"},
                zmin=0, zmax=1,
            )
            fig = styled_plotly(fig)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("**Interpretation**: Higher values indicate stronger price synchronization between stores.")
        else:
            st.info("Cross-store synchronization data not available")
