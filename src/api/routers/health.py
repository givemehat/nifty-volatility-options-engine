"""
Healthcheck and system status router.
"""

from fastapi import APIRouter
from datetime import datetime
from src.common.db import query_df

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def health_check():
    """
    Check system health, database readiness, and latest data timestamps.
    """
    db_status = "connected"
    vol_last_date = None
    options_count = 0
    
    try:
        df_vol = query_df("SELECT MAX(date) as max_date, COUNT(*) as count FROM realized_volatility")
        if not df_vol.empty:
            vol_last_date = str(df_vol["max_date"].iloc[0])
            
        df_opt = query_df("SELECT COUNT(*) as count FROM strangle_screener_ranks")
        if not df_opt.empty:
            options_count = int(df_opt["count"].iloc[0])
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "latest_volatility_date": vol_last_date,
        "active_strangle_candidates": options_count,
        "timestamp": datetime.now().isoformat(),
    }
