"""
API Client for Streamlit Dashboard to interact with the decoupled FastAPI backend.
Includes graceful direct-query fallback if backend is running embedded.
"""

import os
import requests
import pandas as pd
from typing import Dict, List, Any, Optional

DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

class AlphaGreyClient:
    def __init__(self, base_url: str = DEFAULT_API_BASE):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            url = f"{self.base_url}{path}"
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def get_health(self) -> Dict[str, Any]:
        data = self._get("/api/health")
        if data:
            return data
        # Fallback to direct DB query
        from src.common.db import query_df
        try:
            df_vol = query_df("SELECT MAX(date) as max_date FROM realized_volatility")
            df_opt = query_df("SELECT COUNT(*) as count FROM strangle_screener_ranks")
            return {
                "status": "healthy (direct)",
                "database": "connected",
                "latest_volatility_date": str(df_vol["max_date"].iloc[0]) if not df_vol.empty else None,
                "active_strangle_candidates": int(df_opt["count"].iloc[0]) if not df_opt.empty else 0,
            }
        except Exception as e:
            return {"status": "degraded", "database": f"error: {e}"}

    def get_volatility_symbols(self) -> Dict[str, Any]:
        data = self._get("/api/volatility/symbols")
        if data:
            return data
        from src.config import ALL_SYMBOLS, EQUITIES_BY_SECTOR, INDICES, SECTOR_MAP
        return {
            "indices": list(INDICES.keys()),
            "equities_by_sector": EQUITIES_BY_SECTOR,
            "all_symbols": list(ALL_SYMBOLS.keys()),
            "sector_map": SECTOR_MAP,
        }

    def get_rv_history(self, symbol: str, limit: int = 60) -> pd.DataFrame:
        data = self._get("/api/volatility/history", {"symbol": symbol, "limit": limit})
        if data and "data" in data:
            return pd.DataFrame(data["data"])
        from src.common.db import query_df
        df = query_df("SELECT * FROM realized_volatility WHERE symbol = ? ORDER BY date ASC", [symbol])
        if not df.empty and len(df) > limit:
            df = df.iloc[-limit:]
        return df

    def get_forecasts(self, symbol: str, model_name: Optional[str] = None) -> pd.DataFrame:
        params = {"symbol": symbol}
        if model_name:
            params["model_name"] = model_name
        data = self._get("/api/volatility/forecasts", params)
        if data and "data" in data:
            return pd.DataFrame(data["data"])
        from src.common.db import query_df
        if model_name:
            return query_df("SELECT * FROM vol_forecasts WHERE symbol = ? AND model_name = ? ORDER BY date ASC", [symbol, model_name])
        return query_df("SELECT * FROM vol_forecasts WHERE symbol = ? ORDER BY date ASC, model_name ASC", [symbol])

    def get_leaderboard(self, symbol: str) -> pd.DataFrame:
        data = self._get("/api/volatility/leaderboard", {"symbol": symbol})
        if data and "leaderboard" in data:
            return pd.DataFrame(data["leaderboard"])
        from src.common.db import query_df
        return query_df("SELECT * FROM vol_model_leaderboard WHERE symbol = ? ORDER BY qlike ASC", [symbol])

    def get_dm_matrix(self, symbol: str) -> pd.DataFrame:
        data = self._get("/api/volatility/dm-matrix", {"symbol": symbol})
        if data and "dm_results" in data:
            return pd.DataFrame(data["dm_results"])
        from src.common.db import query_df
        return query_df("SELECT * FROM vol_dm_tests WHERE symbol = ?", [symbol])

    def get_options_symbols(self) -> List[str]:
        data = self._get("/api/options/symbols")
        if data and "symbols" in data:
            return data["symbols"]
        from src.common.db import query_df
        df = query_df("SELECT DISTINCT symbol FROM strangle_screener_ranks")
        return list(df["symbol"].unique()) if not df.empty else ["NIFTY", "BANKNIFTY"]

    def get_strangles(
        self,
        symbol: str = "NIFTY",
        min_dte: int = 1,
        max_dte: int = 45,
        min_liquidity: float = 0.0,
        limit: int = 25
    ) -> pd.DataFrame:
        params = {
            "symbol": symbol,
            "min_dte": min_dte,
            "max_dte": max_dte,
            "min_liquidity": min_liquidity,
            "limit": limit
        }
        data = self._get("/api/options/strangles", params)
        if data and "candidates" in data:
            return pd.DataFrame(data["candidates"])
        from src.common.db import query_df
        sql = """
            SELECT * FROM strangle_screener_ranks
            WHERE symbol = ? AND dte >= ? AND dte <= ? AND liquidity_score >= ?
            ORDER BY rank_score DESC LIMIT ?
        """
        return query_df(sql, [symbol, min_dte, max_dte, min_liquidity, limit])

    def get_oi_divergence(self, symbol: str = "NIFTY", anomalies_only: bool = False) -> pd.DataFrame:
        params = {"symbol": symbol, "anomalies_only": anomalies_only}
        data = self._get("/api/options/divergence", params)
        if data and "records" in data:
            return pd.DataFrame(data["records"])
        from src.common.db import query_df
        if anomalies_only:
            return query_df("SELECT * FROM oi_divergence_tracker WHERE symbol = ? AND flag_anomaly = True ORDER BY ABS(divergence_metric) DESC", [symbol])
        return query_df("SELECT * FROM oi_divergence_tracker WHERE symbol = ? ORDER BY strike ASC", [symbol])

    def get_option_chain(self, symbol: str = "NIFTY", expiry: Optional[str] = None) -> pd.DataFrame:
        params = {"symbol": symbol}
        if expiry:
            params["expiry"] = expiry
        data = self._get("/api/options/chain", params)
        if data and "strikes" in data:
            return pd.DataFrame(data["strikes"])
        from src.common.db import query_df
        if expiry:
            return query_df("SELECT * FROM options_chain_snapshots WHERE symbol = ? AND expiry = ? ORDER BY strike ASC", [symbol, expiry])
        return query_df("SELECT * FROM options_chain_snapshots WHERE symbol = ? ORDER BY strike ASC", [symbol])

# Singleton client instance
api_client = AlphaGreyClient()
