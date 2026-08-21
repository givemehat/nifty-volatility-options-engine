"""
Options Liquidity Scorer:
Evaluates Open Interest (OI) depth, volume activity, and bid-ask spread efficiency.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

def compute_strike_liquidity_score(
    oi: int,
    volume: int,
    bid: float,
    ask: float,
    median_oi: float = 100000.0,
    median_vol: float = 50000.0
) -> Dict[str, float]:
    """
    Compute liquidity sub-scores for an individual option strike.
    Returns normalized scores in range [0, 100].
    """
    mid_price = (bid + ask) / 2.0 if (bid + ask) > 0 else 1.0
    spread = max(0.0, ask - bid)
    spread_pct = spread / mid_price if mid_price > 0 else 0.1
    
    # 1. Spread score: tight spread (0% - 1%) = 100, wide spread (> 5%) = 0
    spread_score = float(np.clip(100.0 * (1.0 - spread_pct / 0.05), 0.0, 100.0))
    
    # 2. OI Depth score: logarithmic scaling against median universe OI
    oi_ratio = oi / max(1.0, median_oi)
    oi_score = float(np.clip(50.0 + 25.0 * np.log10(max(0.1, oi_ratio)), 0.0, 100.0))
    
    # 3. Volume score: logarithmic scaling against median universe volume
    vol_ratio = volume / max(1.0, median_vol)
    vol_score = float(np.clip(50.0 + 25.0 * np.log10(max(0.1, vol_ratio)), 0.0, 100.0))
    
    # Weighted composite liquidity score
    composite_liquidity = 0.45 * spread_score + 0.35 * oi_score + 0.20 * vol_score
    
    return {
        "spread_score": round(spread_score, 2),
        "oi_score": round(oi_score, 2),
        "vol_score": round(vol_score, 2),
        "liquidity_score": round(composite_liquidity, 2),
    }

def compute_strangle_liquidity(
    call_oi: int,
    call_vol: int,
    call_bid: float,
    call_ask: float,
    put_oi: int,
    put_vol: int,
    put_bid: float,
    put_ask: float,
    median_oi: float = 100000.0,
    median_vol: float = 50000.0
) -> float:
    """
    Compute harmonic mean / composite liquidity score for a short strangle pair.
    """
    ce_liq = compute_strike_liquidity_score(call_oi, call_vol, call_bid, call_ask, median_oi, median_vol)["liquidity_score"]
    pe_liq = compute_strike_liquidity_score(put_oi, put_vol, put_bid, put_ask, median_oi, median_vol)["liquidity_score"]
    
    # Penalize if one leg is illiquid (minimum of both + average)
    composite = 0.6 * min(ce_liq, pe_liq) + 0.4 * ((ce_liq + pe_liq) / 2.0)
    return round(float(composite), 2)
