"""
Black-Scholes Options Pricing, Implied Volatility Solver, and Analytical Greeks.
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from typing import Dict, Any, Optional, Tuple

def d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
    """Calculate d1 and d2 for Black-Scholes formula."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0, 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return float(d1), float(d2)

def bs_price(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CE") -> float:
    """
    Calculate Black-Scholes option price.
    option_type: 'CE' (Call) or 'PE' (Put)
    """
    if T <= 0:
        if option_type == "CE":
            return max(0.0, S - K)
        else:
            return max(0.0, K - S)
            
    d1, d2 = d1_d2(S, K, T, r, sigma)
    if option_type.upper() in ["CE", "CALL", "C"]:
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return max(0.0, float(price))

def implied_volatility(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float = 0.065,
    option_type: str = "CE",
    default_iv: float = 0.15
) -> float:
    """
    Solve for implied volatility using Brent's root-finding method.
    """
    if price <= 0 or S <= 0 or K <= 0 or T <= 0:
        return default_iv

    intrinsic = max(0.0, S - K) if option_type == "CE" else max(0.0, K - S)
    if price < intrinsic:
        return default_iv

    def objective(sigma):
        return bs_price(S, K, T, r, sigma, option_type) - price

    try:
        # Solve for sigma in reasonable bounds [0.001, 5.0] (0.1% to 500% vol)
        iv = brentq(objective, 0.001, 5.0, maxiter=100, xtol=1e-5)
        return float(iv)
    except Exception:
        return default_iv

def calculate_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "CE"
) -> Dict[str, float]:
    """
    Calculate analytical Black-Scholes Greeks:
    Delta, Gamma, Vega, Theta (daily).
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        is_call = option_type.upper() in ["CE", "CALL", "C"]
        delta = 1.0 if (is_call and S > K) else (-1.0 if (not is_call and S < K) else 0.0)
        return {"delta": delta, "gamma": 0.0, "vega": 0.0, "theta": 0.0}

    d1, d2 = d1_d2(S, K, T, r, sigma)
    pdf_d1 = norm.pdf(d1)
    sqrt_T = np.sqrt(T)

    is_call = option_type.upper() in ["CE", "CALL", "C"]
    
    # Delta
    if is_call:
        delta = norm.cdf(d1)
    else:
        delta = norm.cdf(d1) - 1.0

    # Gamma (identical for Call & Put)
    gamma = pdf_d1 / (S * sigma * sqrt_T)

    # Vega (per 1% change in vol, identical for Call & Put)
    vega = (S * pdf_d1 * sqrt_T) / 100.0

    # Theta (daily decay = annual theta / 365)
    if is_call:
        theta_annual = -(S * pdf_d1 * sigma) / (2.0 * sqrt_T) - r * K * np.exp(-r * T) * norm.cdf(d2)
    else:
        theta_annual = -(S * pdf_d1 * sigma) / (2.0 * sqrt_T) + r * K * np.exp(-r * T) * norm.cdf(-d2)
    theta_daily = theta_annual / 365.0

    return {
        "delta": round(float(delta), 4),
        "gamma": round(float(gamma), 6),
        "vega": round(float(vega), 4),
        "theta": round(float(theta_daily), 4),
    }

def calculate_strangle_profile(
    spot: float,
    call_strike: float,
    put_strike: float,
    call_premium: float,
    put_premium: float,
    price_range_pct: float = 0.15,
    num_points: int = 100
) -> Dict[str, Any]:
    """
    Generate P&L profile and breakeven levels for a short strangle position.
    """
    total_credit = call_premium + put_premium
    lower_be = put_strike - total_credit
    upper_be = call_strike + total_credit

    min_spot = spot * (1.0 - price_range_pct)
    max_spot = spot * (1.0 + price_range_pct)
    spot_range = np.linspace(min_spot, max_spot, num_points)

    # Short Strangle P&L at expiration:
    # PnL = Total Credit - max(0, S_T - K_call) - max(0, K_put - S_T)
    pnl = total_credit - np.maximum(0, spot_range - call_strike) - np.maximum(0, put_strike - spot_range)

    return {
        "spot": spot,
        "call_strike": call_strike,
        "put_strike": put_strike,
        "total_credit": round(total_credit, 2),
        "max_profit": round(total_credit, 2),
        "lower_breakeven": round(lower_be, 2),
        "upper_breakeven": round(upper_be, 2),
        "spot_range": spot_range.tolist(),
        "pnl_profile": pnl.tolist(),
    }
