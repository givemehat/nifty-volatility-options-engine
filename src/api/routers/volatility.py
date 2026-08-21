"""
Volatility Forecasting API Router:
Serves precomputed Realized Volatility series, HAR/ML model forecasts, leaderboards, and DM matrices.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional, List
from src.config import ALL_SYMBOLS, INDICES, EQUITIES_BY_SECTOR, SECTOR_MAP, API_RATE_LIMIT
from src.api.limiter import limiter
from src.api.cache import memory_cache
from src.common.db import query_df

router = APIRouter(prefix="/api/volatility", tags=["Volatility"])

@router.get("/symbols")
@limiter.limit(API_RATE_LIMIT)
def get_symbols(request: Request):
    """
    Get configured universe of indices and equities with sector groupings.
    """
    return {
        "indices": list(INDICES.keys()),
        "equities_by_sector": EQUITIES_BY_SECTOR,
        "all_symbols": list(ALL_SYMBOLS.keys()),
        "sector_map": SECTOR_MAP,
    }

@router.get("/history")
@limiter.limit(API_RATE_LIMIT)
def get_rv_history(
    request: Request,
    symbol: str = Query("NIFTY 50", description="Symbol name e.g. NIFTY 50, RELIANCE"),
    limit: int = Query(60, ge=5, le=500)
):
    """
    Get historical daily Realized Variance, Annualized Volatility, Bipower Variation, and Jump components.
    """
    cache_key = f"rv_hist_{symbol}_{limit}"
    cached = memory_cache.get(cache_key)
    if cached:
        return cached

    sql = """
        SELECT symbol, date, rv_daily, rv_annualized, bv_daily, jump_component, close_price
        FROM realized_volatility
        WHERE symbol = ?
        ORDER BY date ASC
    """
    df = query_df(sql, [symbol])
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No realized volatility history found for symbol '{symbol}'.")

    # Limit to most recent rows if requested
    if len(df) > limit:
        df = df.iloc[-limit:]

    # Convert date to ISO string for JSON serialization
    df["date"] = df["date"].astype(str)
    result = {
        "symbol": symbol,
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }
    memory_cache.set(cache_key, result, ttl=30)
    return result

@router.get("/forecasts")
@limiter.limit(API_RATE_LIMIT)
def get_forecasts(
    request: Request,
    symbol: str = Query("NIFTY 50"),
    model_name: Optional[str] = Query(None, description="Optional filter by model e.g. HAR, LightGBM")
):
    """
    Get out-of-sample forecast vs actual realized volatility series.
    """
    cache_key = f"forecasts_{symbol}_{model_name}"
    cached = memory_cache.get(cache_key)
    if cached:
        return cached

    if model_name:
        sql = """
            SELECT symbol, date, model_name, forecast_rv, actual_rv, forecast_vol, actual_vol
            FROM vol_forecasts
            WHERE symbol = ? AND model_name = ?
            ORDER BY date ASC
        """
        df = query_df(sql, [symbol, model_name])
    else:
        sql = """
            SELECT symbol, date, model_name, forecast_rv, actual_rv, forecast_vol, actual_vol
            FROM vol_forecasts
            WHERE symbol = ?
            ORDER BY date ASC, model_name ASC
        """
        df = query_df(sql, [symbol])

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No forecast data found for symbol '{symbol}'.")

    df["date"] = df["date"].astype(str)
    result = {
        "symbol": symbol,
        "models": list(df["model_name"].unique()),
        "data": df.to_dict(orient="records"),
    }
    memory_cache.set(cache_key, result, ttl=30)
    return result

@router.get("/leaderboard")
@limiter.limit(API_RATE_LIMIT)
def get_leaderboard(
    request: Request,
    symbol: str = Query("NIFTY 50")
):
    """
    Get model performance leaderboard (R2, QLIKE, RMSE, MAE) for a symbol.
    """
    cache_key = f"leaderboard_{symbol}"
    cached = memory_cache.get(cache_key)
    if cached:
        return cached

    sql = """
        SELECT symbol, model_name, r2, qlike, rmse, mae, eval_date
        FROM vol_model_leaderboard
        WHERE symbol = ?
        ORDER BY qlike ASC
    """
    df = query_df(sql, [symbol])
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No leaderboard found for symbol '{symbol}'.")

    df["eval_date"] = df["eval_date"].astype(str)
    result = {
        "symbol": symbol,
        "leaderboard": df.to_dict(orient="records"),
    }
    memory_cache.set(cache_key, result, ttl=30)
    return result

@router.get("/dm-matrix")
@limiter.limit(API_RATE_LIMIT)
def get_dm_matrix(
    request: Request,
    symbol: str = Query("NIFTY 50")
):
    """
    Get pairwise Diebold-Mariano test results matrix.
    """
    cache_key = f"dm_matrix_{symbol}"
    cached = memory_cache.get(cache_key)
    if cached:
        return cached

    sql = """
        SELECT symbol, model_1, model_2, dm_stat, p_value, is_significant, better_model
        FROM vol_dm_tests
        WHERE symbol = ?
    """
    df = query_df(sql, [symbol])
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No DM test results found for symbol '{symbol}'.")

    result = {
        "symbol": symbol,
        "dm_results": df.to_dict(orient="records"),
    }
    memory_cache.set(cache_key, result, ttl=30)
    return result
