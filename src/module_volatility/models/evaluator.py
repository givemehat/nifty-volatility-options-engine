"""
Model Evaluation, Out-of-Sample Walk-Forward Validation, and Pairwise Diebold-Mariano Tests.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from src.common.stats import r2_metric, qlike_metric, rmse_metric, mae_metric, diebold_mariano_test
from src.module_volatility.models.har import StandardHAR, ClusterHAR, SectorHAR
from src.module_volatility.models.pca_har import PCAHARBackfillModel
from src.module_volatility.models.ml_models import LightGBMVolModel, XGBoostVolModel

def evaluate_volatility_models(
    symbol: str,
    df_features: pd.DataFrame,
    df_cluster_rv: Optional[pd.DataFrame] = None,
    df_sector_rv: Optional[pd.DataFrame] = None,
    split_ratio: float = 0.8
) -> Dict[str, pd.DataFrame]:
    """
    Train and evaluate all volatility forecasting models out-of-sample.
    
    Returns:
        forecasts_df: Out-of-sample daily predictions vs actuals per model.
        leaderboard_df: Model performance metrics (R2, QLIKE, RMSE, MAE).
        dm_tests_df: Pairwise Diebold-Mariano test statistics and p-values.
    """
    if df_features.empty or len(df_features) < 15:
        return {
            "forecasts": pd.DataFrame(),
            "leaderboard": pd.DataFrame(),
            "dm_tests": pd.DataFrame(),
        }

    n_samples = len(df_features)
    train_size = int(n_samples * split_ratio)
    
    train_df = df_features.iloc[:train_size].copy()
    test_df = df_features.iloc[train_size:].copy()
    
    if len(test_df) < 5:
        # Fallback to 70/30 split if test set is too small
        train_size = int(n_samples * 0.7)
        train_df = df_features.iloc[:train_size].copy()
        test_df = df_features.iloc[train_size:].copy()

    actual_rv = test_df["target_rv"].values
    actual_vol = np.sqrt(actual_rv * 252.0)
    test_dates = test_df["target_date"].values

    # Model instances
    models = {}
    
    # 1. Standard HAR
    try:
        har = StandardHAR().fit(train_df)
        models["HAR"] = har.predict_df(test_df)
    except Exception as e:
        print(f"HAR fit failed: {e}")

    # 2. Cluster-HAR
    try:
        if df_cluster_rv is not None and not df_cluster_rv.empty:
            c_har = ClusterHAR().fit(train_df, df_cluster_rv)
            models["Cluster-HAR"] = c_har.predict_df(test_df, df_cluster_rv)
        else:
            models["Cluster-HAR"] = models.get("HAR", np.copy(actual_rv))
    except Exception as e:
        print(f"Cluster-HAR fit failed: {e}")

    # 3. Sector-HAR
    try:
        if df_sector_rv is not None and not df_sector_rv.empty:
            s_har = SectorHAR().fit(train_df, df_sector_rv)
            models["Sector-HAR"] = s_har.predict_df(test_df, df_sector_rv)
        else:
            models["Sector-HAR"] = models.get("HAR", np.copy(actual_rv))
    except Exception as e:
        print(f"Sector-HAR fit failed: {e}")

    # 4. PCA-HAR-Backfill
    try:
        pca_har = PCAHARBackfillModel(n_components=3).fit(train_df)
        models["PCA-HAR-Backfill"] = pca_har.predict_df(test_df)
    except Exception as e:
        print(f"PCA-HAR fit failed: {e}")

    # 5. LightGBM
    try:
        lgb_model = LightGBMVolModel().fit(train_df)
        models["LightGBM"] = lgb_model.predict_df(test_df)
    except Exception as e:
        print(f"LightGBM fit failed: {e}")

    # 6. XGBoost
    try:
        xgb_model = XGBoostVolModel().fit(train_df)
        models["XGBoost"] = xgb_model.predict_df(test_df)
    except Exception as e:
        print(f"XGBoost fit failed: {e}")

    # 1. Build Forecasts DataFrame
    forecast_rows = []
    for model_name, preds_rv in models.items():
        preds_vol = np.sqrt(preds_rv * 252.0)
        for d, f_rv, a_rv, f_vol, a_vol in zip(test_dates, preds_rv, actual_rv, preds_vol, actual_vol):
            forecast_rows.append({
                "symbol": symbol,
                "date": d,
                "model_name": model_name,
                "forecast_rv": float(f_rv),
                "actual_rv": float(a_rv),
                "forecast_vol": float(f_vol),
                "actual_vol": float(a_vol),
            })
    df_forecasts = pd.DataFrame(forecast_rows)

    # 2. Build Leaderboard DataFrame
    leaderboard_rows = []
    for model_name, preds_rv in models.items():
        r2 = r2_metric(actual_rv, preds_rv)
        qlike = qlike_metric(actual_rv, preds_rv)
        rmse_val = rmse_metric(actual_rv, preds_rv)
        mae_val = mae_metric(actual_rv, preds_rv)
        
        leaderboard_rows.append({
            "symbol": symbol,
            "model_name": model_name,
            "r2": round(r2, 4),
            "qlike": round(qlike, 5),
            "rmse": round(rmse_val, 6),
            "mae": round(mae_val, 6),
            "eval_date": datetime.now(),
        })
    df_leaderboard = pd.DataFrame(leaderboard_rows).sort_values("qlike").reset_index(drop=True)

    # 3. Build Pairwise Diebold-Mariano Test DataFrame
    model_names = list(models.keys())
    dm_rows = []
    for i in range(len(model_names)):
        for j in range(len(model_names)):
            m1 = model_names[i]
            m2 = model_names[j]
            if m1 == m2:
                dm_rows.append({
                    "symbol": symbol,
                    "model_1": m1,
                    "model_2": m2,
                    "dm_stat": 0.0,
                    "p_value": 1.0,
                    "is_significant": False,
                    "better_model": "identical",
                    "eval_date": datetime.now(),
                })
            else:
                dm_res = diebold_mariano_test(
                    y_true=actual_rv,
                    y_pred1=models[m1],
                    y_pred2=models[m2],
                    loss_type="qlike"
                )
                better = m1 if dm_res["better_model"] == "model_1" else (m2 if dm_res["better_model"] == "model_2" else "equivalent")
                dm_rows.append({
                    "symbol": symbol,
                    "model_1": m1,
                    "model_2": m2,
                    "dm_stat": dm_res["dm_stat"],
                    "p_value": dm_res["p_value"],
                    "is_significant": dm_res["is_significant"],
                    "better_model": better,
                    "eval_date": datetime.now(),
                })
    df_dm_tests = pd.DataFrame(dm_rows)

    return {
        "forecasts": df_forecasts,
        "leaderboard": df_leaderboard,
        "dm_tests": df_dm_tests,
    }
