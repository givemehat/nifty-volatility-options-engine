"""
Streamlit Community Cloud Root Entrypoint for AlphaGrey Platform.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_path = Path(__file__).resolve().parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Run batch pipeline once if database doesn't exist
from src.config import DB_PATH
if not DB_PATH.exists():
    from src.jobs.run_batch import main as run_batch_main
    try:
        from src.module_volatility.pipeline import run_volatility_pipeline
        from src.module_options.pipeline import run_options_pipeline
        run_volatility_pipeline()
        run_options_pipeline()
    except Exception as e:
        print(f"Warning on cloud init: {e}")

# Execute main Streamlit app
import app.main
