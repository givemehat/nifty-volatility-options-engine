"""
Configuration settings for AlphaGrey quantitative analytics engine.
"""

from pathlib import Path
from typing import Dict, List

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Storage directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "database"
DB_PATH = DB_DIR / "alphagrey.duckdb"

# Create directories if they don't exist
for d in [RAW_DATA_DIR / "ohlcv", RAW_DATA_DIR / "options_chain", PROCESSED_DATA_DIR, DB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Ticker universe for Realized Volatility modeling
INDICES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
}

# Top liquid NSE equities with sector classifications
EQUITIES_BY_SECTOR: Dict[str, Dict[str, str]] = {
    "Financials": {
        "HDFCBANK": "HDFCBANK.NS",
        "ICICIBANK": "ICICIBANK.NS",
        "SBIN": "SBIN.NS",
        "KOTAKBANK": "KOTAKBANK.NS",
    },
    "IT": {
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "WIPRO": "WIPRO.NS",
        "HCLTECH": "HCLTECH.NS",
    },
    "Energy & Materials": {
        "RELIANCE": "RELIANCE.NS",
        "ONGC": "ONGC.NS",
        "TATASTEEL": "TATASTEEL.NS",
    },
    "Auto": {
        "TATAMOTORS": "TATAMOTORS.NS",
        "MARUTI": "MARUTI.NS",
        "M&M": "M&M.NS",
    },
    "FMCG & Pharma": {
        "ITC": "ITC.NS",
        "HINDUNILVR": "HINDUNILVR.NS",
        "SUNPHARMA": "SUNPHARMA.NS",
    },
}

# Flattened symbol map for lookups
ALL_SYMBOLS: Dict[str, str] = {**INDICES}
SECTOR_MAP: Dict[str, str] = {}
for sector, stocks in EQUITIES_BY_SECTOR.items():
    for name, sym in stocks.items():
        ALL_SYMBOLS[name] = sym
        SECTOR_MAP[name] = sector

# Volatility Modeling Parameters
VOL_PARAMS = {
    "intraday_interval": "5m",
    "intraday_period": "60d",        # 60 days of 5m intraday data from yfinance
    "daily_period": "2y",            # 2 years of daily data for broad history
    "har_lags": {
        "daily": 1,
        "weekly": 5,
        "monthly": 22,
    },
    "train_test_split_ratio": 0.8,
    "pca_n_components": 3,
}

# Options Screener Parameters
OPTIONS_PARAMS = {
    "indices": ["NIFTY", "BANKNIFTY"],
    "min_open_interest": 50000,
    "delta_target_strangle": 0.15,   # ~15-20 delta strangle
    "delta_tolerance": 0.08,
    "min_dte": 1,
    "max_dte": 35,
    "risk_free_rate": 0.065,         # 6.5% RBI repo rate proxy
}

# API Rate Limiter Defaults
API_RATE_LIMIT = "60/minute"
