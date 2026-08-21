"""
Batch Job CLI Runner for AlphaGrey.
Executes batch ingestion, volatility modeling, and options chain screening.
"""

import sys
import argparse
from datetime import datetime
from src.module_volatility.pipeline import run_volatility_pipeline
from src.module_options.pipeline import run_options_pipeline

def main():
    parser = argparse.ArgumentParser(description="AlphaGrey Batch Analytics Job Runner")
    parser.add_argument(
        "--module",
        choices=["all", "volatility", "options"],
        default="all",
        help="Module to execute: 'all', 'volatility', or 'options'"
    )
    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] Starting AlphaGrey Batch Pipeline (Module: {args.module})...")

    if args.module in ["all", "volatility"]:
        print("\n--- Running Module 1: Realized Volatility Pipeline ---")
        try:
            res_vol = run_volatility_pipeline()
            print(f"Volatility Pipeline Result: {res_vol}")
        except Exception as e:
            print(f"Error in Volatility Pipeline: {e}")

    if args.module in ["all", "options"]:
        print("\n--- Running Module 2: Options Liquidity Pipeline ---")
        try:
            res_opt = run_options_pipeline()
            print(f"Options Pipeline Result: {res_opt}")
        except Exception as e:
            print(f"Error in Options Pipeline: {e}")

    print(f"\n[{datetime.now().isoformat()}] Batch Job Completed Successfully!")

if __name__ == "__main__":
    main()
