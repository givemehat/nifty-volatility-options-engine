"""
Feature Engineering for HAR (Heterogeneous Autoregressive) and ML Volatility Models.
Constructs multi-scale realized variance lags (daily, weekly, monthly) and volatility indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

def create_har_features(
    df_rv: pd.DataFrame,
    target_lead: int = 1,
    daily_lag: int = 1,
    weekly_window: int = 5,
    monthly_window: int = 22
) -> pd.DataFrame:
    """
    Construct HAR feature matrix for a single asset's RV series.
    
    Features:
    - rv_d: Realized variance yesterday (RV_t-1)
    - rv_w: 5-day rolling average realized variance
    - rv_m: 22-day rolling average realized variance
    - bv_d: Bipower variation lag
    - jump_d: Jump component lag
    - jump_ratio: Jump / RV ratio
    - ret_d: Daily closing log return
    - target_rv: Target realized variance for t + target_lead (default t+1)
    - target_vol: Target annualized realized volatility
    """
    if df_rv.empty or len(df_rv) < max(monthly_window, 10):
        return pd.DataFrame()

    df = df_rv.copy().sort_values("date").reset_index(drop=True)
    
    # Base RV series
    rv_series = df["rv_daily"].values
    
    # 1. Daily lag (RV_t)
    rv_d = df["rv_daily"].shift(0)
    
    # 2. Weekly lag (average of past 5 days including today)
    rv_w = df["rv_daily"].rolling(window=weekly_window, min_periods=2).mean()
    
    # 3. Monthly lag (average of past 22 days including today, or shorter min_periods)
    min_m_periods = min(len(df) // 3, monthly_window)
    rv_m = df["rv_daily"].rolling(window=monthly_window, min_periods=min_m_periods).mean()
    
    # Price returns
    if "close_price" in df.columns:
        close_prices = df["close_price"].values
        ret = np.zeros(len(df))
        ret[1:] = np.log(close_prices[1:] / close_prices[:-1])
        df["ret_d"] = ret
    else:
        df["ret_d"] = 0.0

    df["rv_d"] = rv_d
    df["rv_w"] = rv_w
    df["rv_m"] = rv_m
    
    # Jump features
    df["bv_d"] = df["bv_daily"].shift(0) if "bv_daily" in df.columns else df["rv_d"]
    df["jump_d"] = df["jump_component"].shift(0) if "jump_component" in df.columns else 0.0
    df["jump_ratio"] = (df["jump_d"] / (df["rv_d"] + 1e-8)).clip(0.0, 1.0)
    
    # Target: Next day's Realized Variance (t + target_lead)
    df["target_rv"] = df["rv_daily"].shift(-target_lead)
    df["target_vol"] = np.sqrt(df["target_rv"] * 252.0)
    
    # Target date
    df["target_date"] = df["date"].shift(-target_lead)
    
    # Drop NaNs created by rolling windows & lead target
    feature_df = df.dropna(subset=["rv_d", "rv_w", "rv_m", "target_rv"]).reset_index(drop=True)
    return feature_df
