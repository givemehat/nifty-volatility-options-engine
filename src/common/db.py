"""
Embedded DuckDB Database connection manager and schema definitions.
AlphaGrey uses DuckDB for local, high-performance analytical storage without an external DB server.
"""

import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.config import DB_PATH

def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Get a connection to the embedded DuckDB database.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH), read_only=read_only)

def init_database() -> None:
    """
    Initialize all database tables and views if they do not exist.
    """
    conn = get_connection(read_only=False)
    try:
        # Table 1: Realized Variance / Volatility daily timeseries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS realized_volatility (
                symbol VARCHAR,
                date DATE,
                rv_daily DOUBLE,
                rv_weekly DOUBLE,
                rv_monthly DOUBLE,
                rv_annualized DOUBLE,
                bv_daily DOUBLE,
                jump_component DOUBLE,
                close_price DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        """)

        # Table 2: Model Out-of-Sample Forecasts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vol_forecasts (
                symbol VARCHAR,
                date DATE,
                model_name VARCHAR,
                forecast_rv DOUBLE,
                actual_rv DOUBLE,
                forecast_vol DOUBLE,
                actual_vol DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date, model_name)
            )
        """)

        # Table 3: Model Leaderboard & Evaluation Metrics
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vol_model_leaderboard (
                symbol VARCHAR,
                model_name VARCHAR,
                r2 DOUBLE,
                qlike DOUBLE,
                rmse DOUBLE,
                mae DOUBLE,
                eval_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, model_name)
            )
        """)

        # Table 4: Pairwise Diebold-Mariano Test Results
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vol_dm_tests (
                symbol VARCHAR,
                model_1 VARCHAR,
                model_2 VARCHAR,
                dm_stat DOUBLE,
                p_value DOUBLE,
                is_significant BOOLEAN,
                better_model VARCHAR,
                eval_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, model_1, model_2)
            )
        """)

        # Table 5: Options Chain Snapshots & Greeks
        conn.execute("""
            CREATE TABLE IF NOT EXISTS options_chain_snapshots (
                symbol VARCHAR,
                expiry DATE,
                strike DOUBLE,
                option_type VARCHAR,
                spot_price DOUBLE,
                iv DOUBLE,
                delta DOUBLE,
                gamma DOUBLE,
                vega DOUBLE,
                theta DOUBLE,
                open_interest BIGINT,
                oi_change BIGINT,
                volume BIGINT,
                bid DOUBLE,
                ask DOUBLE,
                last_price DOUBLE,
                snapshot_time TIMESTAMP,
                PRIMARY KEY (symbol, expiry, strike, option_type, snapshot_time)
            )
        """)

        # Table 6: Strangle Screener Ranked Candidates
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strangle_screener_ranks (
                id VARCHAR PRIMARY KEY,
                symbol VARCHAR,
                expiry DATE,
                spot_price DOUBLE,
                dte INTEGER,
                call_strike DOUBLE,
                put_strike DOUBLE,
                call_iv DOUBLE,
                put_iv DOUBLE,
                mean_iv DOUBLE,
                call_delta DOUBLE,
                put_delta DOUBLE,
                net_delta DOUBLE,
                strangle_premium DOUBLE,
                premium_pct DOUBLE,
                liquidity_score DOUBLE,
                risk_score DOUBLE,
                rank_score DOUBLE,
                call_oi BIGINT,
                put_oi BIGINT,
                total_oi BIGINT,
                oi_divergence_score DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 7: Intraday OI Divergence Tracker
        conn.execute("""
            CREATE TABLE IF NOT EXISTS oi_divergence_tracker (
                symbol VARCHAR,
                strike DOUBLE,
                option_type VARCHAR,
                spot_price DOUBLE,
                spot_return_pct DOUBLE,
                oi_change_pct DOUBLE,
                divergence_metric DOUBLE,
                flag_anomaly BOOLEAN,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    finally:
        conn.close()

def save_df_to_table(df: pd.DataFrame, table_name: str, mode: str = "overwrite") -> None:
    """
    Save or append a Pandas DataFrame to a DuckDB table.
    mode: 'overwrite' or 'append'
    """
    if df.empty:
        return
    conn = get_connection(read_only=False)
    try:
        if mode == "overwrite":
            conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        else:
            conn.execute(f"INSERT OR REPLACE INTO {table_name} SELECT * FROM df")
    finally:
        conn.close()

def query_df(query_str: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
    """
    Execute a SQL query against DuckDB and return results as a Pandas DataFrame.
    """
    conn = get_connection(read_only=True)
    try:
        if params:
            return conn.execute(query_str, params).fetchdf()
        return conn.execute(query_str).fetchdf()
    finally:
        conn.close()
