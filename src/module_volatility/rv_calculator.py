"""
Realized Variance and Volatility computation from intraday high-frequency log returns.
Implements Realized Variance (RV), Realized Volatility, Bipower Variation (BV), and Jump Decomposition.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional

# Barndorff-Nielsen and Shephard (2004) constant mu_1 = sqrt(2/pi)
MU_1_INV_SQ = np.pi / 2.0  # approximately 1.5707963

def compute_daily_realized_volatility(df_intraday: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily realized variance metrics from intraday OHLCV bars.
    
    Returns DataFrame with columns:
    [symbol, date, rv_daily, rv_annualized, bv_daily, jump_component, close_price]
    """
    if df_intraday.empty:
        return pd.DataFrame()

    df = df_intraday.copy()
    
    # Ensure datetime parsing
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df["date"] = df["datetime"].dt.date
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    else:
        raise ValueError("Intraday data must contain 'datetime' or 'date' column.")

    symbol = df["symbol"].iloc[0] if "symbol" in df.columns else "UNKNOWN"
    df = df.sort_values("datetime" if "datetime" in df.columns else "date")

    daily_results = []
    for day, group in df.groupby("date"):
        if len(group) < 3:  # Need at least a few bars to compute intraday returns
            continue
            
        prices = group["close"].values.astype(float)
        # Avoid division by zero or invalid log
        valid_mask = (prices[:-1] > 0) & (prices[1:] > 0)
        if not np.any(valid_mask):
            continue
            
        log_returns = np.log(prices[1:] / prices[:-1])
        log_returns = log_returns[np.isfinite(log_returns)]
        
        if len(log_returns) < 2:
            continue
            
        # 1. Realized Variance (RV): sum of squared log returns
        rv_daily = float(np.sum(log_returns ** 2))
        
        # 2. Bipower Variation (BV): jump-robust variance
        abs_ret = np.abs(log_returns)
        bv_daily = float(MU_1_INV_SQ * np.sum(abs_ret[1:] * abs_ret[:-1]))
        
        # 3. Jump Component: J_t = max(0, RV_t - BV_t)
        jump_comp = max(0.0, rv_daily - bv_daily)
        
        # 4. Annualized Realized Volatility (assuming 252 trading days)
        rv_ann = float(np.sqrt(rv_daily * 252.0))
        
        last_close = float(prices[-1])
        
        daily_results.append({
            "symbol": symbol,
            "date": day,
            "rv_daily": rv_daily,
            "rv_annualized": rv_ann,
            "bv_daily": bv_daily,
            "jump_component": jump_comp,
            "close_price": last_close,
        })
        
    res_df = pd.DataFrame(daily_results)
    if not res_df.empty:
        res_df = res_df.sort_values("date").reset_index(drop=True)
    return res_df

def compute_realized_volatility_universe(intraday_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Compute daily realized volatility series for all symbols in the universe dictionary.
    """
    rv_dict = {}
    for symbol, df_intraday in intraday_dict.items():
        rv_df = compute_daily_realized_volatility(df_intraday)
        if not rv_df.empty:
            rv_dict[symbol] = rv_df
    return rv_dict
