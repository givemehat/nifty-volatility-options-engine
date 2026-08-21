"""
VolVantage - NIFTY Volatility & Options Liquidity Platform
Streamlit Main Landing Page
"""

import streamlit as st
import pandas as pd
from app.api_client import api_client

st.set_page_config(
    page_title="VolVantage Quantitative Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚡ VolVantage Quantitative Analytics")
st.markdown("### Public NIFTY Volatility Forecasting & Options Liquidity Screener")

# Top Metrics Row
health = api_client.get_health()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="System Status",
        value=health.get("status", "Unknown").upper(),
        delta="Embedded DuckDB"
    )

with col2:
    st.metric(
        label="Database Engine",
        value="DuckDB / Parquet",
        delta="Zero Managed DB Server"
    )

with col3:
    st.metric(
        label="Latest Volatility Date",
        value=health.get("latest_volatility_date", "Live")[:10] if health.get("latest_volatility_date") else "Live",
    )

with col4:
    st.metric(
        label="Ranked Strangles",
        value=health.get("active_strangle_candidates", 0),
        delta="Multi-Factor Ranked"
    )

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("#### 📈 Module 1: Realized Volatility Forecasting")
    st.markdown("""
    - **High-Frequency Ingestion**: 5-minute intraday log returns from NSE index & equity universe.
    - **Realized Volatility & Jump Decomposition**: Computes Daily $RV_t$, Bipower Variation ($BV_t$), and Continuous Jump variation ($J_t$).
    - **Econometric & ML Suite**:
      - **Classic HAR-RV**: Corsi (2009) Heterogeneous Autoregressive model across daily, weekly, and monthly horizons.
      - **Cluster-HAR**: Incorporates return-correlation cluster volatility spillover.
      - **Sector-HAR**: Models cross-asset sector volatility contagion.
      - **PCA-HAR-Backfill**: Latent factor decomposition with reconstructed historical backfilling.
      - **LightGBM & XGBoost**: Gradient boosted regressors capturing non-linear volatility dynamics.
    - **Statistical Significance**: Robust QLIKE loss scoring and pairwise **Diebold-Mariano** hypothesis testing.
    """)
    st.page_link("pages/1_📈_Volatility_Forecast.py", label="👉 Open Volatility Forecasting Dashboard", icon="📈")

with col_right:
    st.markdown("#### ⚡ Module 2: Options Liquidity & Strangle Screener")
    st.markdown("""
    - **Live NSE Options Chain Ingestion**: Ingests strikes, Open Interest, IV, Volume, and Bid/Ask depth.
    - **Analytical Greek Engine**: Black-Scholes Delta ($\Delta$), Gamma ($\Gamma$), Vega ($\mathcal{V}$), Theta ($\Theta$), and exact IV root solver.
    - **Short-Strangle Candidate Generator**:
      - Automated OTM strike filtering by moneyness and delta cushion.
      - Multi-factor ranking balancing **liquidity depth**, **delta neutrality**, and **premium yield**.
    - **Intraday OI Divergence Tracker**:
      - Measures rate of change in Open Interest relative to underlying spot trajectory.
      - Flags anomalous institutional accumulation and writing zones.
    - **Interactive Payoff Visualizer**: Breakeven levels, max credit, and risk-reward profiles.
    """)
    st.page_link("pages/2_⚡_Options_Liquidity_Screener.py", label="👉 Open Options Liquidity Screener", icon="⚡")

st.divider()
st.markdown("##### 🏛️ Architecture Highlights")
st.info("""
- **Stateless & Scalable**: Decoupled FastAPI backend and lightweight Streamlit frontend.
- **Embedded Analytical DB**: File-based DuckDB handles high-throughput queries with zero server overhead.
- **Precomputed Batch Schedule**: Intensive ML model fitting and Greek calculations run asynchronously in batch jobs.
""")
