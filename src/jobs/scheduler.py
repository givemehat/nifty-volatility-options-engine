"""
APScheduler Background Daemon for Automated Market Hours Updates.
"""

import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from src.module_volatility.pipeline import run_volatility_pipeline
from src.module_options.pipeline import run_options_pipeline

def job_update_volatility():
    print(f"[{datetime.datetime.now()}] [CRON] Triggered Realized Volatility Pipeline...")
    try:
        run_volatility_pipeline()
    except Exception as e:
        print(f"Error in scheduled volatility job: {e}")

def job_update_options():
    print(f"[{datetime.datetime.now()}] [CRON] Triggered Options Liquidity Screener Pipeline...")
    try:
        run_options_pipeline()
    except Exception as e:
        print(f"Error in scheduled options job: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Job 1: Update Options Chain & Strangle Screener every 5 minutes
    scheduler.add_job(
        job_update_options,
        trigger=IntervalTrigger(minutes=5),
        id="job_options_5m",
        name="Update Options Chain & Screener",
        replace_existing=True
    )

    # Job 2: Update Realized Volatility & Refit Models every 15 minutes
    scheduler.add_job(
        job_update_volatility,
        trigger=IntervalTrigger(minutes=15),
        id="job_volatility_15m",
        name="Update RV & Refit Forecasting Models",
        replace_existing=True
    )

    scheduler.start()
    print("🚀 AlphaGrey Scheduler Daemon Started.")
    print(" - Options Screener: Every 5 minutes")
    print(" - Volatility Pipeline: Every 15 minutes")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler Daemon stopped.")

if __name__ == "__main__":
    start_scheduler()
