"""
Options Risk Scorer for Short Strangle Portfolios:
Evaluates Delta Neutrality, Vega Exposure, and Moneyness Cushion.
"""

import numpy as np
from typing import Dict, Any

def compute_strangle_risk_metrics(
    spot: float,
    call_strike: float,
    put_strike: float,
    call_delta: float,
    put_delta: float,
    call_vega: float,
    put_vega: float,
    premium: float
) -> Dict[str, float]:
    """
    Compute risk profile and normalized risk score for a short strangle setup.
    Higher score indicates a safer, more delta-neutral, well-cushioned structure.
    """
    # 1. Net Delta bias: ideally 0.0 for a delta-neutral strangle
    net_delta = call_delta + put_delta  # call_delta > 0, put_delta < 0
    delta_score = float(np.clip(100.0 * (1.0 - abs(net_delta) / 0.15), 0.0, 100.0))

    # 2. Strike Width / Cushion: distance between call and put as % of spot
    cushion_pct = (call_strike - put_strike) / spot if spot > 0 else 0.05
    cushion_score = float(np.clip(cushion_pct * 1000.0, 20.0, 100.0))

    # 3. Vega Risk: total vega relative to collected premium
    total_vega = call_vega + put_vega
    vega_to_premium = total_vega / max(1.0, premium)
    vega_score = float(np.clip(100.0 * (1.0 - vega_to_premium / 2.0), 10.0, 100.0))

    # Composite risk score (higher is safer)
    risk_score = 0.45 * delta_score + 0.35 * cushion_score + 0.20 * vega_score

    return {
        "net_delta": round(float(net_delta), 4),
        "total_vega": round(float(total_vega), 4),
        "cushion_pct": round(float(cushion_pct * 100.0), 2),
        "delta_score": round(delta_score, 2),
        "cushion_score": round(cushion_score, 2),
        "vega_score": round(vega_score, 2),
        "risk_score": round(float(risk_score), 2),
    }
