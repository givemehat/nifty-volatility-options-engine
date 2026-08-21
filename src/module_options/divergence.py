"""
Intraday Open Interest (OI) Divergence Metric and Anomaly Detector.
Tracks asymmetric OI buildup relative to underlying spot price movement.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

def compute_oi_divergence(
    df_chain: pd.DataFrame,
    spot_return_pct: float = 0.25,
    anomaly_threshold: float = 20.0
) -> pd.DataFrame:
    """
    Compute OI Divergence metric across all strikes in an option chain.
    
    Formula:
    Divergence = OI_Change_Pct - (Directional_Sign * Spot_Return_Pct * Sensitivity)
    Flags strikes with unusual institutional accumulation / writing.
    """
    if df_chain.empty:
        return pd.DataFrame()

    df = df_chain.copy()
    
    records = []
    for _, row in df.iterrows():
        oi = float(row.get("open_interest", 1))
        oi_change = float(row.get("oi_change", 0))
        strike = float(row.get("strike", 0))
        opt_type = str(row.get("option_type", "CE")).upper()
        spot_price = float(row.get("spot_price", 0))
        symbol = str(row.get("symbol", "NIFTY"))

        # Base OI before change
        base_oi = max(1000.0, oi - oi_change)
        oi_change_pct = (oi_change / base_oi) * 100.0

        # Expected direction of writing:
        # CE writing surges when market is bearish / resistance forms (-1 sign)
        # PE writing surges when market is bullish / support forms (+1 sign)
        sign = 1.0 if opt_type in ["PE", "PUT"] else -1.0
        
        # Divergence metric: positive indicates anomalous accumulation against price trend
        divergence = oi_change_pct - (sign * spot_return_pct * 3.0)
        
        flag_anomaly = abs(divergence) >= anomaly_threshold and abs(oi_change) > 10000

        records.append({
            "symbol": symbol,
            "strike": strike,
            "option_type": opt_type,
            "spot_price": spot_price,
            "spot_return_pct": round(spot_return_pct, 2),
            "oi_change_pct": round(oi_change_pct, 2),
            "divergence_metric": round(divergence, 2),
            "flag_anomaly": bool(flag_anomaly),
            "recorded_at": datetime.now(),
        })

    return pd.DataFrame(records)
