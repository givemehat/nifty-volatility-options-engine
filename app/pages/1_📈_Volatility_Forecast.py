"""
Module 1: Realized Volatility Forecasting Dashboard
Streamlit Page
"""

import streamlit as st
import pandas as pd
from app.api_client import api_client
from app.components.vol_charts import (
    plot_forecast_vs_realized,
    plot_rv_decomposition,
    plot_dm_heatmap,
)

st.set_page_config(
    page_title="Volatility Forecasting | AlphaGrey",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Realized Volatility Forecasting")
st.caption("Econometric HAR Variants (Cluster, Sector, PCA-Backfill) & Machine Learning (LightGBM, XGBoost)")

# 1. Sidebar Controls
st.sidebar.header("Configuration & Asset Selector")

sym_info = api_client.get_volatility_symbols()
all_symbols = sym_info.get("all_symbols", ["NIFTY 50", "BANK NIFTY", "RELIANCE", "TCS", "HDFCBANK"])

selected_symbol = st.sidebar.selectbox(
    "Select Underlying Asset / Index",
    options=all_symbols,
    index=0
)

lookback_days = st.sidebar.slider(
    "Historical Lookback (Days)",
    min_value=15,
    max_value=120,
    value=45,
    step=5
)

# Fetch Data
with st.spinner("Loading precomputed forecasts & model leaderboard..."):
    df_rv = api_client.get_rv_history(selected_symbol, limit=lookback_days)
    df_forecasts = api_client.get_forecasts(selected_symbol)
    df_leaderboard = api_client.get_leaderboard(selected_symbol)
    df_dm = api_client.get_dm_matrix(selected_symbol)

# Model Filter Checkboxes
if not df_forecasts.empty:
    available_models = list(df_forecasts["model_name"].unique())
    selected_models = st.sidebar.multiselect(
        "Select Forecasting Models to Display",
        options=available_models,
        default=available_models
    )
else:
    selected_models = []

# 2. Key Performance Metrics Row
if not df_leaderboard.empty:
    best_model = df_leaderboard.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Top Performing Model", best_model["model_name"])
    with col2:
        st.metric("Best QLIKE Loss", f"{best_model['qlike']:.5f}")
    with col3:
        st.metric("Out-of-Sample R²", f"{best_model['r2']:.4f}")
    with col4:
        st.metric("Out-of-Sample RMSE", f"{best_model['rmse']:.6f}")

st.divider()

# 3. Main Chart: Forecast vs Realized Volatility
st.subheader("🎯 Out-of-Sample Forecast vs Realized Volatility")
if not df_forecasts.empty:
    fig_f = plot_forecast_vs_realized(df_forecasts, selected_models=selected_models)
    st.plotly_chart(fig_f, use_container_width=True)
else:
    st.warning(f"No forecast data available for '{selected_symbol}'. Run batch update job.")

col_left, col_right = st.columns([1, 1])

# 4. Model Leaderboard Table
with col_left:
    st.subheader("🏆 Model Performance Leaderboard")
    st.markdown("*Ranked by Quasi-Likelihood (QLIKE) robust loss (lower is better)*")
    if not df_leaderboard.empty:
        display_df = df_leaderboard.copy()
        display_df.rename(columns={
            "model_name": "Model",
            "r2": "R²",
            "qlike": "QLIKE Loss",
            "rmse": "RMSE",
            "mae": "MAE"
        }, inplace=True)
        cols_to_show = ["Model", "QLIKE Loss", "R²", "RMSE", "MAE"]
        st.dataframe(
            display_df[cols_to_show].style.highlight_min(subset=["QLIKE Loss", "RMSE", "MAE"], color="#2E7D32")
                                     .highlight_max(subset=["R²"], color="#2E7D32"),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Leaderboard not yet computed.")

# 5. Pairwise Diebold-Mariano Tests Matrix
with col_right:
    st.subheader("🔬 Diebold-Mariano Statistical Significance")
    st.markdown("*Tests null hypothesis $H_0: E[d_t]=0$ (equal predictive accuracy). Green/Yellow = statistically distinguishable (p < 0.05)*")
    if not df_dm.empty:
        fig_dm = plot_dm_heatmap(df_dm)
        st.plotly_chart(fig_dm, use_container_width=True)
    else:
        st.info("DM test matrix not yet computed.")

st.divider()

# 6. Realized Volatility & Jump Decomposition
st.subheader("📊 Realized Volatility & Jump Variation Decomposition")
st.markdown("Decomposes daily integrated variance $RV_t$ into continuous diffusion (Bipower Variation $BV_t$) and jump anomalies $J_t = \\max(0, RV_t - BV_t)$.")
if not df_rv.empty:
    fig_rv = plot_rv_decomposition(df_rv)
    st.plotly_chart(fig_rv, use_container_width=True)
else:
    st.info("No historical RV data found.")
