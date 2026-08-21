"""
Batch Pipeline Orchestrator for Realized Volatility Forecasting.
Ingests intraday bars, computes RV, fits HAR/ML models, computes Diebold-Mariano tests,
and saves results to embedded DuckDB.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from src.config import ALL_SYMBOLS, SECTOR_MAP, VOL_PARAMS
from src.common.db import init_database, save_df_to_table
from src.ingestion.ohlcv_fetcher import fetch_all_universe
from src.module_volatility.rv_calculator import compute_realized_volatility_universe
from src.module_volatility.clustering import (
    build_correlation_clusters,
    compute_cluster_rv_series,
    compute_sector_rv_series,
)
from src.module_volatility.features import create_har_features
from src.module_volatility.models.evaluator import evaluate_volatility_models

def run_volatility_pipeline(symbols_dict: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Execute complete batch run for Realized Volatility forecasting module.
    """
    print("Initializing DuckDB schema...")
    init_database()

    symbols = symbols_dict or ALL_SYMBOLS
    print(f"Step 1: Ingesting intraday OHLCV for {len(symbols)} symbols...")
    intraday_data = fetch_all_universe(symbols)

    print("Step 2: Computing Realized Variance (RV) & Jump components...")
    rv_dict = compute_realized_volatility_universe(intraday_data)

    # Save all RV series to DuckDB
    all_rv_dfs = []
    for sym, df_rv in rv_dict.items():
        all_rv_dfs.append(df_rv)
    if all_rv_dfs:
        combined_rv_df = pd.concat(all_rv_dfs, ignore_index=True)
        save_df_to_table(combined_rv_df, "realized_volatility", mode="overwrite")
        print(f"Saved {len(combined_rv_df)} daily RV records to DuckDB.")

    print("Step 3: Building correlation clusters and sector RV aggregates...")
    cluster_map, corr_matrix = build_correlation_clusters(rv_dict, n_clusters=3)
    cluster_rv_series = compute_cluster_rv_series(rv_dict, cluster_map)
    sector_rv_series = compute_sector_rv_series(rv_dict, SECTOR_MAP)

    print("Step 4: Fitting HAR, Cluster-HAR, Sector-HAR, PCA-HAR, LightGBM, and XGBoost models...")
    all_forecasts = []
    all_leaderboards = []
    all_dm_tests = []

    for sym, df_rv in rv_dict.items():
        df_features = create_har_features(df_rv)
        if df_features.empty or len(df_features) < 10:
            print(f"Skipping {sym}: insufficient historical observations.")
            continue

        cluster_id = cluster_map.get(sym, 0)
        df_c_rv = cluster_rv_series.get(cluster_id)
        sector_name = SECTOR_MAP.get(sym)
        df_s_rv = sector_rv_series.get(sector_name) if sector_name else None

        eval_res = evaluate_volatility_models(
            symbol=sym,
            df_features=df_features,
            df_cluster_rv=df_c_rv,
            df_sector_rv=df_s_rv,
            split_ratio=VOL_PARAMS["train_test_split_ratio"]
        )

        if not eval_res["forecasts"].empty:
            all_forecasts.append(eval_res["forecasts"])
        if not eval_res["leaderboard"].empty:
            all_leaderboards.append(eval_res["leaderboard"])
        if not eval_res["dm_tests"].empty:
            all_dm_tests.append(eval_res["dm_tests"])

    print("Step 5: Persisting forecasts, leaderboard, and DM matrices to DuckDB...")
    if all_forecasts:
        df_f = pd.concat(all_forecasts, ignore_index=True)
        save_df_to_table(df_f, "vol_forecasts", mode="overwrite")
        print(f"Persisted {len(df_f)} forecast predictions.")

    if all_leaderboards:
        df_l = pd.concat(all_leaderboards, ignore_index=True)
        save_df_to_table(df_l, "vol_model_leaderboard", mode="overwrite")
        print(f"Persisted model leaderboard for {len(all_leaderboards)} assets.")

    if all_dm_tests:
        df_dm = pd.concat(all_dm_tests, ignore_index=True)
        save_df_to_table(df_dm, "vol_dm_tests", mode="overwrite")
        print(f"Persisted pairwise Diebold-Mariano test results.")

    print("✅ Volatility Pipeline Completed Successfully!")
    return {
        "status": "success",
        "symbols_processed": list(rv_dict.keys()),
        "forecasts_count": sum(len(f) for f in all_forecasts),
    }

if __name__ == "__main__":
    run_volatility_pipeline()
