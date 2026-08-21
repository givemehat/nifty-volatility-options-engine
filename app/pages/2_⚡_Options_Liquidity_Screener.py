"""
Module 2: Options Liquidity & Short-Strangle Screener
Streamlit Page
"""

import streamlit as st
import pandas as pd
from app.api_client import api_client
from app.components.options_charts import (
    plot_strangle_payoff,
    plot_oi_divergence_chart,
    plot_oi_distribution,
)
from src.common.greeks import calculate_strangle_profile

st.set_page_config(
    page_title="Options Liquidity Screener | AlphaGrey",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Options Liquidity & Short-Strangle Screener")
st.caption("Multi-factor Liquidity & Delta-Neutrality Ranking for Indian Index & Equity Options")

# Sidebar Filters
st.sidebar.header("Screener Filters")

available_symbols = api_client.get_options_symbols()
selected_symbol = st.sidebar.selectbox("Select Asset / Index", options=available_symbols, index=0)

col_dte1, col_dte2 = st.sidebar.columns(2)
with col_dte1:
    min_dte = st.number_input("Min DTE", min_value=0, max_value=90, value=1)
with col_dte2:
    max_dte = st.number_input("Max DTE", min_value=1, max_value=90, value=45)

min_liquidity = st.sidebar.slider("Min Liquidity Score (0-100)", min_value=0.0, max_value=100.0, value=30.0, step=5.0)
top_n_limit = st.sidebar.slider("Max Candidates", min_value=5, max_value=50, value=20, step=5)

# Fetch Data
with st.spinner("Fetching precomputed strangle candidates & options chain..."):
    df_strangles = api_client.get_strangles(
        symbol=selected_symbol,
        min_dte=int(min_dte),
        max_dte=int(max_dte),
        min_liquidity=float(min_liquidity),
        limit=int(top_n_limit)
    )
    df_div = api_client.get_oi_divergence(selected_symbol)
    df_chain = api_client.get_option_chain(selected_symbol)

# Top Summary Row
if not df_strangles.empty:
    top_cand = df_strangles.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Top Setup Rank Score", f"{top_cand['rank_score']:.1f}/100")
    with c2:
        st.metric("Strangle Premium", f"₹{top_cand['strangle_premium']:.2f}", f"{top_cand['premium_pct']:.2f}% of spot")
    with c3:
        st.metric("Net Delta", f"{top_cand['net_delta']:+.4f}", "Delta Neutral")
    with c4:
        st.metric("Liquidity Score", f"{top_cand['liquidity_score']:.1f}/100")

st.divider()

# 1. Main Ranked Table
st.subheader(f"🎯 Ranked Short-Strangle Setups for {selected_symbol}")
st.markdown("*Rank Score combines **Liquidity Depth (40%)**, **Risk & Delta Balance (35%)**, and **Premium Yield (25%)**.*")

if not df_strangles.empty:
    display_cols = [
        "id", "expiry", "dte", "spot_price", "call_strike", "put_strike",
        "strangle_premium", "premium_pct", "net_delta", "mean_iv",
        "liquidity_score", "risk_score", "rank_score"
    ]
    cols_present = [c for c in display_cols if c in df_strangles.columns]
    
    formatted_df = df_strangles[cols_present].copy()
    formatted_df.rename(columns={
        "expiry": "Expiry",
        "dte": "DTE",
        "spot_price": "Spot (₹)",
        "call_strike": "Call K",
        "put_strike": "Put K",
        "strangle_premium": "Total Credit (₹)",
        "premium_pct": "Yield %",
        "net_delta": "Net Delta",
        "mean_iv": "Mean IV",
        "liquidity_score": "Liquidity",
        "risk_score": "Safety Score",
        "rank_score": "Rank Score"
    }, inplace=True)

    st.dataframe(
        formatted_df.drop(columns=["id"], errors="ignore").style.highlight_max(subset=["Rank Score", "Liquidity", "Safety Score"], color="#1B5E20"),
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No strangle setups matched your filter criteria.")

st.divider()

# 2. Interactive Payoff Profile Analyzer
st.subheader("📊 Strangle Expiration Payoff & Risk Profile")
if not df_strangles.empty:
    candidate_options = df_strangles["id"].tolist()
    selected_id = st.selectbox(
        "Select Strangle Candidate to Visualize Payoff Profile",
        options=candidate_options,
        index=0,
        format_func=lambda x: f"Setup: Put {x.split('_')[-1]} / Call {x.split('_')[-2]} (Expiry: {x.split('_')[1]})"
    )

    cand_row = df_strangles[df_strangles["id"] == selected_id].iloc[0]
    
    # Calculate payoff curve
    profile = calculate_strangle_profile(
        spot=float(cand_row["spot_price"]),
        call_strike=float(cand_row["call_strike"]),
        put_strike=float(cand_row["put_strike"]),
        call_premium=float(cand_row["strangle_premium"] / 2.0),
        put_premium=float(cand_row["strangle_premium"] / 2.0),
    )

    col_chart, col_stats = st.columns([2, 1])

    with col_chart:
        fig_payoff = plot_strangle_payoff(profile)
        st.plotly_chart(fig_payoff, use_container_width=True)

    with col_stats:
        st.markdown("##### 📌 Setup Diagnostics")
        st.write(f"**Spot Price:** ₹{cand_row['spot_price']:,.2f}")
        st.write(f"**Put Strike (Short):** ₹{cand_row['put_strike']:,.0f}")
        st.write(f"**Call Strike (Short):** ₹{cand_row['call_strike']:,.0f}")
        st.write(f"**Collected Premium:** ₹{cand_row['strangle_premium']:,.2f}")
        st.write(f"**Lower Breakeven:** ₹{profile['lower_breakeven']:,.2f}")
        st.write(f"**Upper Breakeven:** ₹{profile['upper_breakeven']:,.2f}")
        st.write(f"**Net Directional Delta:** `{cand_row['net_delta']:+.4f}`")
        st.write(f"**Average Implied Volatility:** `{cand_row['mean_iv']*100:.2f}%`")
        st.write(f"**Total Open Interest:** `{int(cand_row.get('total_oi', 0)):,} contracts`")

st.divider()

# 3. Intraday OI Divergence & Anomaly Detection
st.subheader("🔍 Intraday Open Interest Divergence & Institutional Writing Zones")
st.markdown("Identifies strikes where Open Interest change diverged significantly from price direction (institutional writing / support-resistance formation).")

col_div, col_oi = st.columns(2)

with col_div:
    if not df_div.empty:
        fig_div = plot_oi_divergence_chart(df_div)
        st.plotly_chart(fig_div, use_container_width=True)
    else:
        st.info("No OI divergence data recorded.")

with col_oi:
    if not df_chain.empty:
        fig_oi = plot_oi_distribution(df_chain)
        st.plotly_chart(fig_oi, use_container_width=True)
    else:
        st.info("No options chain snapshot recorded.")
