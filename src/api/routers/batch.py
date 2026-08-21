"""
Batch Trigger Router:
Allows on-demand triggering of background data refresh jobs.
"""

from fastapi import APIRouter, BackgroundTasks, Request
from src.api.limiter import limiter
from src.api.cache import memory_cache
from src.module_volatility.pipeline import run_volatility_pipeline
from src.module_options.pipeline import run_options_pipeline

router = APIRouter(prefix="/api/batch", tags=["Batch"])

@router.post("/refresh-volatility")
@limiter.limit("5/minute")
def trigger_volatility_refresh(background_tasks: BackgroundTasks, request: Request):
    """
    Trigger background update for Realized Volatility data and HAR/ML models.
    """
    def _task():
        run_volatility_pipeline()
        memory_cache.clear()

    background_tasks.add_task(_task)
    return {"status": "accepted", "message": "Volatility pipeline batch job dispatched in background."}

@router.post("/refresh-options")
@limiter.limit("10/minute")
def trigger_options_refresh(background_tasks: BackgroundTasks, request: Request):
    """
    Trigger background update for NSE options chain and strangle screener.
    """
    def _task():
        run_options_pipeline()
        memory_cache.clear()

    background_tasks.add_task(_task)
    return {"status": "accepted", "message": "Options pipeline batch job dispatched in background."}
