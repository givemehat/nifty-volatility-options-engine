"""
Options Liquidity and Short-Strangle Screener API Router.
Serves ranked strangle setups, Greeks, P&L payoff curves, and intraday OI divergence metrics.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional, List
from src.config import OPTIONS_PARAMS, API_RATE_LIMIT
from src.api.limiter import limiter
from src.api.cache import memory_cache
from src.common.db import query_df
from src.common.greeks import calculate_strangle_profile

router = APIRouter(prefix="/api/options", tags=["Options"])

@router.get("/symbols")
@limiter.limit(API_RATE_LIMIT)
def get_options_symbols(request: Request):
    """
    Get available symbols for options liquidity screening.
    """
    sql = "SELECT DISTINCT symbol FROM strangle_screener_ranks"
    df = query_df(sql)
    symbols = list(df["symbol"].unique()) if not df.empty else ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK"]
    return {"symbols": symbols}

@router.get("/strangles")
@limiter.limit(API_RATE_LIMIT)
def get_strangles(
    request: Request,
    symbol: Optional[str] = Query("NIFTY", description="Asset symbol e.g. NIFTY, BANKNIFTY"),
    min_dte: int = Query(1, ge=0),
    max_dte: int = Query(45, le=100),
    min_liquidity: float = Query(0.0, ge=0.0, le=100.0),
    limit: int = Query(25, ge=1, le=100)
):
    """
    Get ranked short-strangle candidates matching criteria.
    """
    cache_key = f"strangles_{symbol}_{min_dte}_{max_dte}_{min_liquidity}_{limit}"
    cached = memory_cache.get(cache_key)
    if cached:
        return cached

    conditions = ["dte >= ?", "dte <= ?", "liquidity_score >= ?"]
    params = [min_dte, max_dte, min_liquidity]

    if symbol and symbol.upper() != "ALL":
        conditions.append("symbol = ?")
        params.append(symbol.upper())

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT *
        FROM strangle_screener_ranks
        WHERE {where_clause}
        ORDER BY rank_score DESC
        LIMIT {limit}
    """
    df = query_df(sql, params)
    if df.empty:
        return {"count": 0, "candidates": []}

    df["expiry"] = df["expiry"].astype(str)
    df["created_at"] = df["created_at"].astype(str)

    result = {
        "count": len(df),
        "candidates": df.to_dict(orient="records"),
    }
    memory_cache.set(cache_key, result, ttl=15)
    return result

@router.get("/strangle-payoff")
@limiter.limit(API_RATE_LIMIT)
def get_strangle_payoff(
    request: Request,
    spot: float = Query(..., description="Current spot price"),
    call_strike: float = Query(..., description="Short Call strike"),
    put_strike: float = Query(..., description="Short Put strike"),
    call_premium: float = Query(..., description="Call option premium"),
    put_premium: float = Query(..., description="Put option premium"),
    price_range_pct: float = Query(0.12, description="Price range fraction for curve")
):
    """
    Calculate expiration P&L profile, max profit, and lower/upper breakeven levels for a strangle.
    """
    profile = calculate_strangle_profile(
        spot=spot,
        call_strike=call_strike,
        put_strike=put_strike,
        call_premium=call_premium,
        put_premium=put_premium,
        price_range_pct=price_range_pct
    )
    return profile

@router.get("/divergence")
@limiter.limit(API_RATE_LIMIT)
def get_oi_divergence(
    request: Request,
    symbol: str = Query("NIFTY"),
    anomalies_only: bool = Query(False)
):
    """
    Get intraday OI Divergence metrics and anomaly flags across strikes.
    """
    cache_key = f"divergence_{symbol}_{anomalies_only}"
    cached = memory_cache.get(cache_key)
    if cached:
        return cached

    if anomalies_only:
        sql = """
            SELECT symbol, strike, option_type, spot_price, spot_return_pct, oi_change_pct, divergence_metric, flag_anomaly, recorded_at
            FROM oi_divergence_tracker
            WHERE symbol = ? AND flag_anomaly = True
            ORDER BY ABS(divergence_metric) DESC
        """
    else:
        sql = """
            SELECT symbol, strike, option_type, spot_price, spot_return_pct, oi_change_pct, divergence_metric, flag_anomaly, recorded_at
            FROM oi_divergence_tracker
            WHERE symbol = ?
            ORDER BY strike ASC, option_type ASC
        """
    df = query_df(sql, [symbol.upper()])
    if df.empty:
        return {"symbol": symbol, "count": 0, "records": []}

    df["recorded_at"] = df["recorded_at"].astype(str)
    result = {
        "symbol": symbol,
        "count": len(df),
        "records": df.to_dict(orient="records"),
    }
    memory_cache.set(cache_key, result, ttl=15)
    return result

@router.get("/chain")
@limiter.limit(API_RATE_LIMIT)
def get_option_chain(
    request: Request,
    symbol: str = Query("NIFTY"),
    expiry: Optional[str] = Query(None)
):
    """
    Get complete option chain ladder with Greeks for strike-by-strike inspection.
    """
    cache_key = f"chain_{symbol}_{expiry}"
    cached = memory_cache.get(cache_key)
    if cached:
        return cached

    if expiry:
        sql = """
            SELECT * FROM options_chain_snapshots
            WHERE symbol = ? AND expiry = ?
            ORDER BY strike ASC, option_type ASC
        """
        df = query_df(sql, [symbol.upper(), expiry])
    else:
        sql = """
            SELECT * FROM options_chain_snapshots
            WHERE symbol = ?
            ORDER BY expiry ASC, strike ASC, option_type ASC
        """
        df = query_df(sql, [symbol.upper()])

    if df.empty:
        return {"symbol": symbol, "count": 0, "strikes": []}

    df["expiry"] = df["expiry"].astype(str)
    df["snapshot_time"] = df["snapshot_time"].astype(str)

    result = {
        "symbol": symbol,
        "count": len(df),
        "strikes": df.to_dict(orient="records"),
    }
    memory_cache.set(cache_key, result, ttl=15)
    return result
