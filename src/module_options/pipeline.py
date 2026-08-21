"""
Batch Pipeline Orchestrator for Options Liquidity & Strangle Screener Module.
Fetches NSE option chains, parses analytical Greeks, computes OI divergence,
generates ranked short strangles, and persists results to embedded DuckDB.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from src.config import OPTIONS_PARAMS
from src.common.db import init_database, save_df_to_table
from src.ingestion.options_fetcher import fetch_nse_option_chain, parse_option_chain_df
from src.module_options.divergence import compute_oi_divergence
from src.module_options.strangle_screener import generate_strangle_candidates

DEFAULT_OPTIONS_SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK"]

def run_options_pipeline(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Execute complete batch run for Options Liquidity & Strangle Screener module.
    """
    print("Initializing DuckDB schema...")
    init_database()

    target_symbols = symbols or DEFAULT_OPTIONS_SYMBOLS
    print(f"Step 1: Fetching option chains for {target_symbols}...")
    
    all_chain_dfs = []
    all_divergence_dfs = []
    all_strangle_dfs = []

    for sym in target_symbols:
        print(f"Fetching & processing options chain for {sym}...")
        raw_chain = fetch_nse_option_chain(sym)
        df_chain = parse_option_chain_df(raw_chain, symbol=sym)

        if df_chain.empty:
            print(f"Warning: Empty option chain for {sym}.")
            continue

        all_chain_dfs.append(df_chain)

        # Step 2: Compute OI Divergence
        df_div = compute_oi_divergence(df_chain, spot_return_pct=0.35)
        if not df_div.empty:
            all_divergence_dfs.append(df_div)

        # Step 3: Generate and Rank Short Strangles
        df_strangles = generate_strangle_candidates(
            df_chain=df_chain,
            min_oi=20000,
            min_delta=0.07,
            max_delta=0.32,
            top_n=25
        )
        if not df_strangles.empty:
            all_strangle_dfs.append(df_strangles)

    print("Step 4: Persisting options data to DuckDB...")
    if all_chain_dfs:
        combined_chain = pd.concat(all_chain_dfs, ignore_index=True)
        save_df_to_table(combined_chain, "options_chain_snapshots", mode="overwrite")
        print(f"Persisted {len(combined_chain)} option strikes.")

    if all_divergence_dfs:
        combined_div = pd.concat(all_divergence_dfs, ignore_index=True)
        save_df_to_table(combined_div, "oi_divergence_tracker", mode="overwrite")
        print(f"Persisted {len(combined_div)} OI divergence records.")

    if all_strangle_dfs:
        combined_strangles = pd.concat(all_strangle_dfs, ignore_index=True)
        save_df_to_table(combined_strangles, "strangle_screener_ranks", mode="overwrite")
        print(f"Persisted {len(combined_strangles)} ranked short strangle candidates.")

    print("✅ Options Liquidity Pipeline Completed Successfully!")
    return {
        "status": "success",
        "symbols_processed": target_symbols,
        "strangles_count": sum(len(s) for s in all_strangle_dfs),
    }

if __name__ == "__main__":
    run_options_pipeline()
