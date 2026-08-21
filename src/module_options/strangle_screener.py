"""
Short-Strangle Candidate Generator and Multi-Factor Ranking Engine.
Filters liquid OTM strikes, pairs delta-balanced strangles, and ranks candidates on liquidity, risk, and yield.
"""

import uuid
import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from src.config import OPTIONS_PARAMS
from src.module_options.liquidity_scorer import compute_strangle_liquidity
from src.module_options.risk_scorer import compute_strangle_risk_metrics

def generate_strangle_candidates(
    df_chain: pd.DataFrame,
    min_oi: int = 25000,
    min_delta: float = 0.08,
    max_delta: float = 0.30,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Generate and rank candidate short strangle setups from an option chain snapshot.
    """
    if df_chain.empty:
        return pd.DataFrame()

    candidates = []
    
    # Process per expiry
    for (symbol, expiry), group in df_chain.groupby(["symbol", "expiry"]):
        spot = group["spot_price"].iloc[0]
        
        # DTE
        if isinstance(expiry, str):
            exp_date = datetime.datetime.strptime(expiry, "%Y-%m-%d").date()
        else:
            exp_date = expiry
        dte = max(1, (exp_date - datetime.date.today()).days)

        # Filter candidate Calls (OTM, Delta in range, min OI)
        calls = group[
            (group["option_type"] == "CE") &
            (group["strike"] > spot) &
            (group["delta"] >= min_delta) &
            (group["delta"] <= max_delta) &
            (group["open_interest"] >= min_oi)
        ]

        # Filter candidate Puts (OTM, Delta in range, min OI)
        puts = group[
            (group["option_type"] == "PE") &
            (group["strike"] < spot) &
            (group["delta"] <= -min_delta) &
            (group["delta"] >= -max_delta) &
            (group["open_interest"] >= min_oi)
        ]

        if calls.empty or puts.empty:
            continue

        median_oi = float(group["open_interest"].median())
        median_vol = float(group["volume"].median())

        for _, ce in calls.iterrows():
            for _, pe in puts.iterrows():
                ce_mid = (ce["bid"] + ce["ask"]) / 2.0
                pe_mid = (pe["bid"] + pe["ask"]) / 2.0
                premium = ce_mid + pe_mid
                premium_pct = (premium / spot) * 100.0

                # Liquidity evaluation
                liq_score = compute_strangle_liquidity(
                    call_oi=int(ce["open_interest"]),
                    call_vol=int(ce["volume"]),
                    call_bid=float(ce["bid"]),
                    call_ask=float(ce["ask"]),
                    put_oi=int(pe["open_interest"]),
                    put_vol=int(pe["volume"]),
                    put_bid=float(pe["bid"]),
                    put_ask=float(pe["ask"]),
                    median_oi=median_oi,
                    median_vol=median_vol
                )

                # Risk evaluation
                risk_metrics = compute_strangle_risk_metrics(
                    spot=spot,
                    call_strike=float(ce["strike"]),
                    put_strike=float(pe["strike"]),
                    call_delta=float(ce["delta"]),
                    put_delta=float(pe["delta"]),
                    call_vega=float(ce["vega"]),
                    put_vega=float(pe["vega"]),
                    premium=premium
                )

                # Yield score (higher premium yield % normalized)
                yield_score = float(np.clip(premium_pct * 35.0, 0.0, 100.0))

                # Composite Rank Score (Multi-Factor Model)
                rank_score = (
                    0.40 * liq_score +
                    0.35 * risk_metrics["risk_score"] +
                    0.25 * yield_score
                )

                mean_iv = (float(ce["iv"]) + float(pe["iv"])) / 2.0
                tot_oi = int(ce["open_interest"]) + int(pe["open_interest"])

                cand_id = f"{symbol}_{exp_date}_{int(ce['strike'])}_{int(pe['strike'])}"

                candidates.append({
                    "id": cand_id,
                    "symbol": symbol,
                    "expiry": exp_date,
                    "spot_price": spot,
                    "dte": dte,
                    "call_strike": float(ce["strike"]),
                    "put_strike": float(pe["strike"]),
                    "call_iv": float(ce["iv"]),
                    "put_iv": float(pe["iv"]),
                    "mean_iv": round(mean_iv, 4),
                    "call_delta": float(ce["delta"]),
                    "put_delta": float(pe["delta"]),
                    "net_delta": risk_metrics["net_delta"],
                    "strangle_premium": round(premium, 2),
                    "premium_pct": round(premium_pct, 2),
                    "liquidity_score": liq_score,
                    "risk_score": risk_metrics["risk_score"],
                    "rank_score": round(rank_score, 2),
                    "call_oi": int(ce["open_interest"]),
                    "put_oi": int(pe["open_interest"]),
                    "total_oi": tot_oi,
                    "oi_divergence_score": round(float(abs(ce.get("oi_change", 0) - pe.get("oi_change", 0)) / max(1, tot_oi) * 100.0), 2),
                    "created_at": datetime.datetime.now(),
                })

    df_cand = pd.DataFrame(candidates)
    if not df_cand.empty:
        df_cand = df_cand.sort_values("rank_score", ascending=False).head(top_n).reset_index(drop=True)
    return df_cand
